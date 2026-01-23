from flask import Flask, render_template, request, redirect, session
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

ADMIN_USER = "admin" 

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

products = []

@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open("users.txt", "a+") as f:
            f.seek(0)
            users = f.read().splitlines()
            if username in [u.split(",")[0] for u in users]:
                return "<h3>User already exists! Please <a href='/login_page'>log in</a></h3>"

            f.write(f"{username},{password}\n")

        session["user"] = username
        if "cart" not in session:
            session["cart"] = []
        return redirect("/products")
    return render_template("register.html")

@app.route("/login_page", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open("users.txt", "r") as f:
            users = [line.strip().split(",") for line in f.readlines()]

        if [username, password] in users:
            session["user"] = username
            if "cart" not in session:
                session["cart"] = []
            return redirect("/products")
        else:
            return "<h3>Invalid username or password. <a href='/login_page'>Try again</a></h3>"

    return render_template("login.html")

@app.route("/products")
def products_page():
    if "user" not in session:
        return redirect("/")

    category = request.args.get("category")
    if category:
        filtered_products = [p for p in products if p["category"] == category]
    else:
        filtered_products = products

    return render_template("products.html", products=filtered_products, current_category=category)

@app.route("/product/<int:index>", methods=["GET", "POST"])
def product_details(index):
    if "user" not in session:
        return redirect("/")

    if index < 0 or index >= len(products):
        return "Product not found"

    product = products[index]

    if request.method == "POST":
        action = request.form["action"]
        if "cart" not in session:
            session["cart"] = []

        if action == "add_to_cart":
            session["cart"].append(index)
            session.modified = True
            return redirect("/cart")
        elif action == "buy_now":
            return f"<h2>Thank you for buying {product['name']}!</h2><a href='/products'>Back to Products</a>"

    return render_template("product_details.html", product=product, index=index)

@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/")
    cart_products = [products[i] for i in session.get("cart", [])]
    return render_template("cart.html", cart_products=cart_products)

@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        image = request.files["image"]

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(image_path)

        products.append({
            "name": request.form["name"],
            "price": request.form["price"],
            "image": filename,
            "category": request.form["category"],
            "size": request.form.get("size", "Standard"),
            "color": request.form.get("color", "Standard"),
            "includes": request.form.get("includes", "")
        })

        return redirect("/products")

    return render_template("add_product.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or session["user"] != ADMIN_USER:
        return "<h3>Access denied. You are not admin.</h3>"

    banned_message = ""
    if request.method == "POST":
        if "ban_user" in request.form:
            username_to_ban = request.form["ban_user"]
            with open("users.txt", "r") as f:
                users = f.readlines()
            with open("users.txt", "w") as f:
                for line in users:
                    if line.strip().split(",")[0] != username_to_ban:
                        f.write(line)
            banned_message = f"User '{username_to_ban}' has been banned."

        elif "remove_product" in request.form:
            index = int(request.form["remove_product"])
            if 0 <= index < len(products):
                removed_name = products[index]["name"]
                products.pop(index)
                banned_message = f"Product '{removed_name}' removed."

    with open("users.txt", "r") as f:
        users_list = [line.strip().split(",")[0] for line in f.readlines()]

    return render_template("admin.html", users=users_list, products=products, message=banned_message)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)