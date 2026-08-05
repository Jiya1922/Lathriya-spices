/* ===========================
      CHANGE PRICE
=========================== */

const weightButtons = document.querySelectorAll(".weight-btn");
const price = document.getElementById("price");

weightButtons.forEach(button => {
    button.addEventListener("click", () => {
        weightButtons.forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");
        price.innerHTML = "₹" + button.dataset.price;
    });
});


/* ===========================
      QUANTITY
=========================== */

const minus = document.getElementById("minus");
const plus = document.getElementById("plus");
const quantity = document.getElementById("quantity");

let count = 1;

plus.addEventListener("click", () => {
    count++;
    quantity.value = count;
});

minus.addEventListener("click", () => {
    if (count > 1) {
        count--;
        quantity.value = count;
    }
});


/* ===========================
      CHANGE PRODUCT IMAGE
=========================== */

function changeImage(image) {

    document.getElementById("mainImage").src = image.src;

    document.querySelectorAll(".thumb").forEach(function(item) {
        item.classList.remove("active-thumb");
    });

    image.classList.add("active-thumb");
}


/* ===========================
      PRODUCT INFORMATION TABS
=========================== */

function showTab(tabId, button) {

    document.querySelectorAll(".tab-content").forEach(function(content) {
        content.classList.remove("active-content");
    });

    document.querySelectorAll(".tab-btn").forEach(function(btn) {
        btn.classList.remove("active");
    });

    document.getElementById(tabId).classList.add("active-content");
    button.classList.add("active");
}
document.getElementById("cartBtn").addEventListener("click", function () {
    window.location.href = "/cart";
});

document.getElementById("buyBtn").addEventListener("click", function () {
    window.location.href = "/checkout";
});