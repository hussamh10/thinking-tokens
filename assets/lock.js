(function () {
  function getMeta(name) {
    var m = document.querySelector('meta[name="' + name + '"]');
    return m ? m.getAttribute('content') : null;
  }

  var pagePassword = getMeta('page-password');       // from front matter
  var adminPassword = getMeta('admin-password');     // from mkdocs.yml
  var pageKey = 'unlocked:' + location.pathname;     // session key per-page

  // If no page password, nothing to do
  if (!pagePassword) {
    return;
  }

  // Already unlocked this page this session?
  if (sessionStorage.getItem(pageKey) === '1') {
    document.documentElement.removeAttribute('data-locked');
    return;
  }

  // Prompt loop (simple, blocking)
  // You can replace prompt() with a custom modal if you want nicer UX.
  var ok = false;
  for (var tries = 0; tries < 5; tries++) {
    var input = window.prompt('This page is locked. Enter password:');
    if (input === null) break;  // user cancelled

    if ((adminPassword && input === adminPassword) || input === pagePassword) {
      ok = true;
      break;
    } else {
      alert('Incorrect password. Try again.');
    }
  }

  if (ok) {
    sessionStorage.setItem(pageKey, '1');
    document.documentElement.removeAttribute('data-locked');
  } else {
    // Stay hidden. Optionally show a tiny message:
    document.body.innerHTML = '<div style="padding:2rem;font-family:system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;">Access denied.</div>';
  }
})();

