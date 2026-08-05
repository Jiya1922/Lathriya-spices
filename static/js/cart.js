// =============================
// Quantity Controls
// =============================

const plus=document.getElementById("plus");
const minus=document.getElementById("minus");
const qty=document.getElementById("qty");
const subtotal=document.getElementById("subtotal");
const total=document.getElementById("total");
let quantity=1;
const unitPrice=250;
plus.addEventListener("click",function(){
quantity++;
updateCart();
});
minus.addEventListener("click",function(){
if(quantity>1){
quantity--;
updateCart();
}
});
function updateCart(){
qty.value=quantity;
let price=quantity*unitPrice;
subtotal.innerHTML="₹"+price;
total.innerHTML="₹"+price;
}
// =============================
// Remove Item
// =============================
const removeBtn=document.querySelector(".remove-btn");
const cartItem=document.querySelector(".cart-item");
removeBtn.addEventListener("click",function(){
if(confirm("Remove this product from cart?")){
cartItem.remove();
subtotal.innerHTML="₹0";
total.innerHTML="₹0";
}
});