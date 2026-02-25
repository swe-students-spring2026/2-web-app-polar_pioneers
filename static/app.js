/* ResumeGo — minimal JS helpers */

function clearField(id) {
  var el = document.getElementById(id);
  if (el) { el.value = ''; el.dispatchEvent(new Event('input')); }
}

function updateCounter(el, counterId, max) {
  var counter = document.getElementById(counterId);
  if (counter) {
    var len = el.value.length;
    counter.textContent = len.toLocaleString() + ' / ' + max.toLocaleString();
    counter.classList.toggle('over-limit', len > max);
  }
}

function showLoading() {
  var overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.style.display = 'flex';
}

function showToast(msg) {
  var toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(function() { toast.classList.add('toast--visible'); }, 10);
  setTimeout(function() {
    toast.classList.remove('toast--visible');
    setTimeout(function() { toast.remove(); }, 300);
  }, 2500);
}

/* Auto-dismiss flash messages after 5s */
document.addEventListener('DOMContentLoaded', function() {
  var flashes = document.querySelectorAll('.flash');
  flashes.forEach(function(f) {
    setTimeout(function() {
      f.style.opacity = '0';
      setTimeout(function() { f.remove(); }, 300);
    }, 5000);
  });
});
