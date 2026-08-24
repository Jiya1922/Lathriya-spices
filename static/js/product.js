document.addEventListener("DOMContentLoaded", function() {
    var weightButtons = document.querySelectorAll(".weight-btn");
    var price = document.getElementById("price");
    var selectedVariantId = null;

    function getMaxStock() {
        var active = document.querySelector(".weight-btn.active");
        if (active && active.dataset.stock !== undefined && active.dataset.stock !== "") {
            var parsed = parseInt(active.dataset.stock);
            if (!isNaN(parsed)) return parsed;
        }
        return 9999;
    }

    function updateStockBadge(stock) {
        var container = document.getElementById("stockBadgeContainer");
        if (!container) return;
        var stockNum = parseInt(stock);
        if (isNaN(stockNum)) stockNum = 0;

        if (stockNum <= 0) {
            container.innerHTML = '<span class="badge bg-danger-subtle text-danger border border-danger-subtle px-3 py-2 rounded-pill fw-bold fs-7" id="stockBadge">' +
                '<i class="fa-solid fa-circle-xmark me-1"></i> Out of Stock</span>';
        } else if (stockNum <= 10) {
            container.innerHTML = '<span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle px-3 py-2 rounded-pill fw-bold fs-7" id="stockBadge">' +
                '<i class="fa-solid fa-fire text-danger me-1"></i> Only <span id="stockVal">' + stockNum + '</span> units left in stock!</span>';
        } else {
            container.innerHTML = '<span class="badge bg-success-subtle text-success border border-success-subtle px-3 py-2 rounded-pill fw-bold fs-7" id="stockBadge">' +
                '<i class="fa-solid fa-circle-check me-1"></i> <span id="stockVal">' + stockNum + '</span> units available in stock</span>';
        }
    }

    weightButtons.forEach(function(button) {
        button.addEventListener("click", function() {
            weightButtons.forEach(function(btn) { btn.classList.remove("active"); });
            button.classList.add("active");
            if (price && button.dataset.price) price.innerHTML = "\u20B9" + parseFloat(button.dataset.price).toFixed(2);
            selectedVariantId = button.dataset.variantId;
            
            // Reset quantity to 1 when changing weight
            count = 1;
            if (quantity) quantity.value = 1;

            // Sync stock badge display & colors
            if (button.dataset.stock !== undefined) {
                updateStockBadge(button.dataset.stock);
            }
        });
    });

    var activeBtn = document.querySelector(".weight-btn.active");
    if (activeBtn) {
        selectedVariantId = activeBtn.dataset.variantId;
        if (activeBtn.dataset.stock !== undefined) {
            updateStockBadge(activeBtn.dataset.stock);
        }
    }

    /* QUANTITY */
    var minus = document.getElementById("minus");
    var plus = document.getElementById("plus");
    var quantity = document.getElementById("quantity");
    var count = 1;
    if (plus && quantity) {
        plus.addEventListener("click", function() {
            var maxStock = getMaxStock();
            if (maxStock <= 0) {
                var outMsg = "Sorry, this product variant is currently out of stock!";
                if (window.showToast) {
                    window.showToast(outMsg, true);
                } else {
                    alert(outMsg);
                }
                return;
            }
            if (count >= maxStock) {
                var excMsg = "Only " + maxStock + " unit(s) available in stock.";
                if (window.showToast) {
                    window.showToast(excMsg, true);
                } else {
                    alert(excMsg);
                }
                return;
            }
            count++;
            quantity.value = count;
        });
    }
    if (minus && quantity) {
        minus.addEventListener("click", function() {
            if (count > 1) {
                count--;
                quantity.value = count;
            }
        });
    }

    function getSelectedVariantId() {
        if (selectedVariantId) return selectedVariantId;
        var active = document.querySelector(".weight-btn.active");
        if (active && active.dataset.variantId) return active.dataset.variantId;
        var firstBtn = document.querySelector(".weight-btn");
        if (firstBtn && firstBtn.dataset.variantId) return firstBtn.dataset.variantId;
        return null;
    }

    /* ADD TO CART */
    var cartBtn = document.getElementById("cartBtn");
    if (cartBtn) {
        cartBtn.addEventListener("click", function(e) {
            if (e) e.preventDefault();
            var targetVariantId = getSelectedVariantId();
            if (!targetVariantId) {
                if (window.showToast) window.showToast("Please select a weight option.", true);
                else alert("Please select a weight option.");
                return;
            }
            
            var qtyVal = quantity ? parseInt(quantity.value || 1) : 1;
            var active = document.querySelector(".weight-btn.active");
            var selectedWeight = active ? active.dataset.weight || "50g" : "50g";
            var prodName = document.querySelector(".product-title") ? document.querySelector(".product-title").textContent.trim() : "Product";

            var maxStock = parseInt(active ? active.dataset.stock : "9999");
            if (isNaN(maxStock)) maxStock = 9999;

            if (maxStock <= 0) {
                var outMsg = "Sorry, " + prodName + " (" + selectedWeight + ") is currently out of stock!";
                if (window.showToast) window.showToast(outMsg, true);
                else alert(outMsg);
                return;
            }

            if (qtyVal > maxStock) {
                var excMsg = "Only " + maxStock + " unit(s) available in stock for " + prodName + " (" + selectedWeight + ").";
                if (window.showToast) window.showToast(excMsg, true);
                else alert(excMsg);
                return;
            }

            var origHtml = cartBtn.innerHTML;
            cartBtn.disabled = true;
            cartBtn.style.opacity = "0.85";
            cartBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin me-1"></i> Adding to Cart...';

            function restoreCartBtn() {
                cartBtn.disabled = false;
                cartBtn.style.opacity = "";
                cartBtn.innerHTML = origHtml;
            }

            fetch("/api/cart/add/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
                body: JSON.stringify({ variant_id: targetVariantId, quantity: qtyVal })
            })
            .then(function(r) {
                if (r.status === 401) {
                    restoreCartBtn();
                    handleLoginRequired(window.location.pathname);
                    return null;
                }
                return r.json();
            })
            .then(function(data) {
                if (!data) return;
                if (data.login_required) {
                    restoreCartBtn();
                    handleLoginRequired(window.location.pathname);
                    return;
                }
                if (data.success) {
                    if (typeof window.updateVariantStockOnPage === "function" && data.remaining_stock !== undefined) {
                        window.updateVariantStockOnPage(data.variant_id || targetVariantId, data.remaining_stock);
                    }

                    var badge = document.querySelector(".cart-count");
                    if (badge) {
                        badge.textContent = data.cart_count;
                        badge.style.transform = "scale(1.3)";
                        setTimeout(function() { badge.style.transform = ""; }, 300);
                    }
                    cartBtn.disabled = false;
                    cartBtn.style.opacity = "";
                    cartBtn.innerHTML = '<i class="fa-solid fa-circle-check me-1"></i> Added to Cart!';
                    cartBtn.style.background = "#2e7d32";

                    if (window.showToast) {
                        window.showToast("Added " + qtyVal + "x " + prodName + " (" + selectedWeight + ") to cart!");
                    }

                    setTimeout(function() {
                        cartBtn.innerHTML = origHtml;
                        cartBtn.style.background = "";
                    }, 1800);
                } else {
                    restoreCartBtn();
                    if (window.showToast) {
                        window.showToast(data.error || "Failed to add to cart.", true);
                    } else {
                        alert(data.error || "Failed to add to cart.");
                    }
                }
            })
            .catch(function(err) {
                console.error(err);
                restoreCartBtn();
                if (window.showToast) {
                    window.showToast("Failed to add to cart.", true);
                } else {
                    alert("Failed to add to cart.");
                }
            });
        });
    }

    /* BUY NOW */
    function performBuyNow() {
        var buyBtn = document.getElementById("buyBtn");
        if (!buyBtn) return;
        var targetVariantId = getSelectedVariantId();
        if (!targetVariantId) {
            if (window.showToast) window.showToast("Please select a weight option.", true);
            else alert("Please select a weight option.");
            return;
        }

        var qtyVal = quantity ? parseInt(quantity.value || 1) : 1;
        var active = document.querySelector(".weight-btn.active");
        var selectedWeight = active ? active.dataset.weight || "50g" : "50g";
        var prodName = document.querySelector(".product-title") ? document.querySelector(".product-title").textContent.trim() : "Product";

        var maxStock = parseInt(active ? active.dataset.stock : "9999");
        if (isNaN(maxStock)) maxStock = 9999;

        if (maxStock <= 0) {
            var outMsg = "Sorry, " + prodName + " (" + selectedWeight + ") is currently out of stock!";
            if (window.showToast) window.showToast(outMsg, true);
            else alert(outMsg);
            return;
        }

        if (qtyVal > maxStock) {
            var excMsg = "Only " + maxStock + " unit(s) available in stock for " + prodName + " (" + selectedWeight + ").";
            if (window.showToast) window.showToast(excMsg, true);
            else alert(excMsg);
            return;
        }

        // Instant visual feedback for 0ms tap delay
        var origHtml = buyBtn.getAttribute("data-orig") || buyBtn.innerHTML;
        if (!buyBtn.getAttribute("data-orig")) buyBtn.setAttribute("data-orig", origHtml);
        
        buyBtn.disabled = true;
        buyBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin me-1"></i> Processing...';
        buyBtn.style.opacity = "0.85";

        function restoreBuyBtn() {
            buyBtn.disabled = false;
            buyBtn.innerHTML = buyBtn.getAttribute("data-orig") || origHtml;
            buyBtn.style.opacity = "";
        }

        fetch("/api/cart/add/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
            body: JSON.stringify({ variant_id: targetVariantId, quantity: qtyVal, is_buy_now: true })
        })
        .then(function(r) {
            if (r.status === 401) {
                restoreBuyBtn();
                handleLoginRequired("/checkout/");
                return null;
            }
            return r.json();
        })
        .then(function(data) {
            if (!data) return;
            if (data.login_required) {
                restoreBuyBtn();
                handleLoginRequired("/checkout/");
                return;
            }
            if (data.success) {
                buyBtn.innerHTML = '<i class="fa-solid fa-check me-1"></i> Redirecting...';
                window.location.href = "/checkout/";
            } else {
                restoreBuyBtn();
                if (window.showToast) {
                    window.showToast(data.error || "Sorry, item is currently out of stock.", true);
                } else {
                    alert(data.error || "Sorry, item is currently out of stock.");
                }
            }
        })
        .catch(function(err) {
            console.error(err);
            restoreBuyBtn();
            if (window.showToast) {
                window.showToast("Something went wrong. Please try again.", true);
            } else {
                alert("Something went wrong. Please try again.");
            }
        });
    }

    var buyBtn = document.getElementById("buyBtn");
    if (buyBtn) {
        buyBtn.addEventListener("click", function(e) {
            if (e) e.preventDefault();
            performBuyNow();
        });
    }

    // Auto-trigger Buy Now if url parameter ?buy_now=1 exists
    var searchParams = new URLSearchParams(window.location.search);
    if (searchParams.get("buy_now") === "1" || searchParams.get("buy_now") === "true") {
        performBuyNow();
    }
});

function handleLoginRequired(targetNextUrl) {
    var redirectUrl = targetNextUrl || ("/accounts/google/login/?next=" + encodeURIComponent(window.location.pathname));
    var modalBtn = document.getElementById("modalGoogleLoginBtn");
    if (modalBtn) {
        modalBtn.href = "/accounts/google/login/?next=" + encodeURIComponent(targetNextUrl || window.location.pathname);
    }
    var modalEl = document.getElementById("authModal");
    if (modalEl && typeof bootstrap !== "undefined") {
        var modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
    } else {
        window.location.href = redirectUrl;
    }
}

/* CHANGE PRODUCT IMAGE */
function changeImage(image) {
    var main = document.getElementById("mainImage");
    if (main) main.src = image.src;
    document.querySelectorAll(".thumb").forEach(function(item) { item.classList.remove("active-thumb"); });
    image.classList.add("active-thumb");
}

/* PRODUCT TABS */
function showTab(tabId, button) {
    document.querySelectorAll(".tab-content").forEach(function(c) { c.classList.remove("active-content"); });
    document.querySelectorAll(".tab-btn").forEach(function(b) { b.classList.remove("active"); });
    var target = document.getElementById(tabId);
    if (target) target.classList.add("active-content");
    if (button) button.classList.add("active");
}

/* CSRF HELPER */
function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
}
