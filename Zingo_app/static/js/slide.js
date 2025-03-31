$(document).ready(function () {
    $('.slick-slider-container').slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        arrows: true,
        dots: true,
        infinite: false,
        prevArrow: '<button class="slick-prev">&lt;</button>',
        nextArrow: '<button class="slick-next">&gt;</button>',
    });
});
