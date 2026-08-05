from flask import Flask, render_template

app = Flask(__name__)

app.secret_key = "lathriya_secret_key"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/shop")
def shop():
    return render_template("shop.html")


@app.route("/product")
def product():
    return render_template("product.html")


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/shipping")
def shipping():
    return render_template("shipping.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


if __name__ == "__main__":
    app.run(debug=True)