const btnR = document.querySelector('.btn-right');
const btnL = document.querySelector('.btn-left');
const tracks = document.querySelector('.tracks');
const tracksW = tracks.scrollWidth;

let scrollInterval; // Variable to hold the interval for continuous scrolling

btnR.addEventListener('mousedown', () => {
  // Start scrolling to the right continuously
  scrollInterval = setInterval(() => {
    tracks.scrollBy({
      left: tracksW / 120, // Adjust the scroll speed as needed
       // Add smooth behavior
    });
  }, 50); // Adjust the interval as needed for the desired scrolling speed
});

btnL.addEventListener('mousedown', () => {
  // Start scrolling to the left continuously
  scrollInterval = setInterval(() => {
    tracks.scrollBy({
      left: -tracksW / 120, // Adjust the scroll speed as needed
     // Add smooth behavior
    });
  }, 50); // Adjust the interval as needed for the desired scrolling speed
});

// Stop scrolling when the mouse button is released
document.addEventListener('mouseup', () => {
  clearInterval(scrollInterval);
});
