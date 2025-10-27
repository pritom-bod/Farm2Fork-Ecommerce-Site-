// shop/static/js/main.js
(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner(0);


    // Fixed Navbar
    $(window).scroll(function () {
        if ($(window).width() < 992) {
            if ($(this).scrollTop() > 55) {
                $('.fixed-top').addClass('shadow');
            } else {
                $('.fixed-top').removeClass('shadow');
            }
        } else {
            if ($(this).scrollTop() > 55) {
                $('.fixed-top').addClass('shadow').css('top', -55);
            } else {
                $('.fixed-top').removeClass('shadow').css('top', 0);
            }
        } 
    });
    
    
   // Back to top button
   $(window).scroll(function () {
    if ($(this).scrollTop() > 300) {
        $('.back-to-top').fadeIn('slow');
    } else {
        $('.back-to-top').fadeOut('slow');
    }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });


    // Testimonial carousel
    $(".testimonial-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 2000,
        center: false,
        dots: true,
        loop: true,
        margin: 25,
        nav : true,
        navText : [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ],
        responsiveClass: true,
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:1
            },
            992:{
                items:2
            },
            1200:{
                items:2
            }
        }
    });


    // vegetable carousel
    $(".vegetable-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        center: false,
        dots: true,
        loop: true,
        margin: 25,
        nav : true,
        navText : [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ],
        responsiveClass: true,
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:3
            },
            1200:{
                items:4
            }
        }
    });


    // Modal Video
    $(document).ready(function () {
        var $videoSrc;
        $('.btn-play').click(function () {
            $videoSrc = $(this).data("src");
        });
        console.log($videoSrc);

        $('#videoModal').on('shown.bs.modal', function (e) {
            $("#video").attr('src', $videoSrc + "?autoplay=1&amp;modestbranding=1&amp;showinfo=0");
        })

        $('#videoModal').on('hide.bs.modal', function (e) {
            $("#video").attr('src', $videoSrc);
        })
    });



    // Product Quantity
    $('.quantity button').on('click', function () {
        var button = $(this);
        var oldValue = button.parent().parent().find('input').val();
        if (button.hasClass('btn-plus')) {
            var newVal = parseFloat(oldValue) + 1;
        } else {
            if (oldValue > 0) {
                var newVal = parseFloat(oldValue) - 1;
            } else {
                newVal = 0;
            }
        }
        button.parent().parent().find('input').val(newVal);
    });

    // CSRF Token Helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Add to Cart AJAX
    $('.add-to-cart').on('click', function (e) {
        e.preventDefault();
        var product_id = $(this).data('product-id');
        $.ajax({
            url: '/add-to-cart/',
            method: 'POST',
            data: { product_id: product_id, quantity: 1 },
            headers: { 'X-CSRFToken': csrftoken },
            success: function (data) {
                if (data.success) {
                    alert('Product added to cart!');
                    // Optionally update cart count in navbar if you add one
                } else if (data.redirect) {
                    alert('Login required');
                    window.location.href = data.redirect;
                } else {
                    alert('Error adding to cart.');
                }
            },
            error: function () {
                alert('Request failed.');
            }
        });
    });

    // Cart Page AJAX for + / -
    $('.btn-plus, .btn-minus').on('click', function (e) {
        e.preventDefault();
        var button = $(this);
        var row = button.closest('tr');
        var item_id = row.data('item-id');
        var action = button.data('action');
        $.ajax({
            url: '/update-cart-item/',
            method: 'POST',
            data: { item_id: item_id, action: action },
            headers: { 'X-CSRFToken': csrftoken },
            success: function (data) {
                if (data.success) {
                    row.find('.quantity-input').val(data.new_quantity);
                    row.find('.item-total').text('$' + data.subtotal);
                    $('.cart-total').text('$' + data.cart_total);
                } else if (data.redirect) {
                    alert('Login required');
                    window.location.href = data.redirect;
                } else {
                    alert('Error updating quantity.');
                }
            },
            error: function () {
                alert('Request failed.');
            }
        });
    });

    // Remove Item AJAX
    $('.remove-item').on('click', function (e) {
        e.preventDefault();
        var button = $(this);
        var row = button.closest('tr');
        var item_id = row.data('item-id');
        $.ajax({
            url: '/remove-from-cart/',
            method: 'POST',
            data: { item_id: item_id },
            headers: { 'X-CSRFToken': csrftoken },
            success: function (data) {
                if (data.success) {
                    row.remove();
                    $('.cart-total').text('$' + data.cart_total);
                    if ($('tbody tr').length === 0) {
                        $('tbody').append('<tr><td colspan="6">Your cart is empty.</td></tr>');
                    }
                } else if (data.redirect) {
                    alert('Login required');
                    window.location.href = data.redirect;
                } else {
                    alert('Error removing item.');
                }
            },
            error: function () {
                alert('Request failed.');
            }
        });
    });

})(jQuery);