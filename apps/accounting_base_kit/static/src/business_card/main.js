var cardflip = document.querySelector('.cardflip');
var corners = document.querySelectorAll('.corner');
corners.forEach(function (corner) {
    corner.addEventListener('click', function () {
        cardflip.classList.toggle('is-flipped');
    })
});