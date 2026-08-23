/* CART PAGE JS — quantity +/-, remove, live totals */

function getCookie(name) {
    var cookieValue = "";
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    if (!cookieValue) {
        var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) cookieValue = csrfInput.value;
    }
    if (!cookieValue && window.getCookie) {
        cookieValue = window.getCookie(name);
    }
    return cookieValue || "";
}

function updateTotals(subtotal) {
    var formatted = parseFloat(subtotal || 0).toFixed(2);
    var subEl = document.getElementById("subtotal");
    if (subEl) subEl.textContent = "\u20B9" + formatted;
    var totEl = document.getElementById("total");
    if (totEl) totEl.textContent = "\u20B9" + formatted;
    var badge = document.querySelector(".cart-count");
    if (badge) {
        var sum = 0;
        document.querySelectorAll(".qty-input").forEach(function(inp) {
            sum += parseInt(inp.value || 0);
        });
        badge.textContent = sum;
    }
}

function apiPost(url, data, callback) {
    var token = getCookie("csrftoken");
    fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": token },
        body: JSON.stringify(data)
    })
    .then(function(r) {
        if (r.status === 401) {
            window.location.href = "/accounts/google/login/?next=" + encodeURIComponent(window.location.pathname);
            return null;
        }
        return r.json();
    })
    .then(function(res) {
        if (!res) return;
        if (res.login_required) {
            window.location.href = "/accounts/google/login/?next=" + encodeURIComponent(window.location.pathname);
            return;
        }
        if (callback) callback(res);
    })
    .catch(function(err) {
        console.error(err);
        if (callback) callback({ success: false, error: "Network or server error." });
    });
}

function removeItem(vid) {
    apiPost("/api/cart/remove/", { variant_id: vid }, function(data) {
        if (data.success) {
            var el = document.querySelector('.cart-item[data-variant-id="' + vid + '"]');
            if (el) {
                el.style.opacity = "0";
                el.style.transform = "translateX(40px)";
                el.style.transition = ".3s";
                setTimeout(function() { el.remove(); }, 300);
            }
            setTimeout(function() {
                if (document.querySelectorAll(".cart-item").length <= 1) {
                    location.reload();
                }
            }, 400);
            updateTotals(data.subtotal);
        }
    });
}

document.addEventListener("DOMContentLoaded", function() {
    /* QUANTITY PLUS */
    document.querySelectorAll(".qty-plus").forEach(function(btn) {
        btn.addEventListener("click", function() {
            var vid = this.dataset.variant;
            var input = document.querySelector('.qty-input[data-variant="' + vid + '"]');
            if (!input) return;
            var newQty = parseInt(input.value || 1) + 1;
            apiPost("/api/cart/update/", { variant_id: vid, quantity: newQty }, function(data) {
                if (data.success) {
                    input.value = newQty;
                    updateTotals(data.subtotal);
                }
            });
        });
    });

    /* QUANTITY MINUS */
    document.querySelectorAll(".qty-minus").forEach(function(btn) {
        btn.addEventListener("click", function() {
            var vid = this.dataset.variant;
            var input = document.querySelector('.qty-input[data-variant="' + vid + '"]');
            if (!input) return;
            var newQty = parseInt(input.value || 1) - 1;
            if (newQty <= 0) {
                removeItem(vid);
                return;
            }
            apiPost("/api/cart/update/", { variant_id: vid, quantity: newQty }, function(data) {
                if (data.success) {
                    input.value = newQty;
                    updateTotals(data.subtotal);
                }
            });
        });
    });

    /* REMOVE BUTTON */
    document.querySelectorAll(".remove-btn").forEach(function(btn) {
        btn.addEventListener("click", function() {
            if (this.dataset.variant) removeItem(this.dataset.variant);
        });
    });

    /* CLEAR CART BUTTON */
    var clearCartBtn = document.getElementById("clearCartBtn");
    if (clearCartBtn) {
        clearCartBtn.addEventListener("click", function() {
            if (!confirm("Are you sure you want to clear your cart? All reserved items will be released back to stock.")) {
                return;
            }
            clearCartBtn.disabled = true;
            clearCartBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin me-1"></i> Clearing...';

            apiPost("/api/cart/clear/", {}, function(data) {
                if (data.success) {
                    var badge = document.querySelector(".cart-count");
                    if (badge) badge.textContent = "0";
                    if (window.showToast) {
                        window.showToast("Cart cleared successfully!");
                    }
                    setTimeout(function() {
                        location.reload();
                    }, 400);
                } else {
                    clearCartBtn.disabled = false;
                    clearCartBtn.innerHTML = '<i class="fa-solid fa-trash-can me-1"></i> Clear Cart';
                    alert(data.error || "Failed to clear cart.");
                }
            });
        });
    }
});
