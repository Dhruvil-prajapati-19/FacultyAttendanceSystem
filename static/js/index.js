  document.addEventListener('DOMContentLoaded', function() {
    var modals = document.querySelectorAll('#qrCodeModal, #qrModal');

    modals.forEach(function(modal) {
        var header = modal.querySelector('.modal-header');
        var posX = 0, posY = 0, posX1 = 0, posY1 = 0;

        header.addEventListener('mousedown', dragMouseDown);

        function dragMouseDown(e) {
            e.preventDefault();
            posX1 = e.clientX;
            posY1 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e.preventDefault();
            posX = posX1 - e.clientX;
            posY = posY1 - e.clientY;
            posX1 = e.clientX;
            posY1 = e.clientY;
            modal.style.top = (modal.offsetTop - posY) + "px";
            modal.style.left = (modal.offsetLeft - posX) + "px";
        }

        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    });
});


