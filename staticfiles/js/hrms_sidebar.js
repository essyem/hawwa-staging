// Simple sidebar pin/unpin and collapse behavior
// Stores state in localStorage so user preference persists across pages
(function () {
  const ROOT = document.documentElement;
  const PIN_KEY = 'hawwa.sidebar.pinned';
  const COLLAPSE_KEY = 'hawwa.sidebar.collapsed';

  function setPinned(pinned) {
    if (pinned) {
      ROOT.classList.add('hawwa-sidebar-pinned');
      ROOT.classList.remove('hawwa-sidebar-hidden');
      localStorage.setItem(PIN_KEY, '1');
      document.getElementById('hawwa-sidebar-pin').setAttribute('aria-pressed', 'true');
      document.getElementById('hawwa-sidebar-pin-icon').classList.add('text-primary');
    } else {
      ROOT.classList.remove('hawwa-sidebar-pinned');
      // when unpinned, hide the sidebar but show mini-strip
      ROOT.classList.add('hawwa-sidebar-hidden');
      localStorage.removeItem(PIN_KEY);
      document.getElementById('hawwa-sidebar-pin').setAttribute('aria-pressed', 'false');
      document.getElementById('hawwa-sidebar-pin-icon').classList.remove('text-primary');
    }
  }

  function setCollapsed(collapsed) {
    if (collapsed) {
      ROOT.classList.add('sidebar-collapsed');
      localStorage.setItem(COLLAPSE_KEY, '1');
      // also ensure sidebar is visible in collapsed mode
      ROOT.classList.remove('hawwa-sidebar-hidden');
    } else {
      ROOT.classList.remove('sidebar-collapsed');
      localStorage.removeItem(COLLAPSE_KEY);
    }
  }

  function init() {
    const pinBtn = document.getElementById('hawwa-sidebar-pin');
    if (!pinBtn) return;

    // Initialize from localStorage
    const pinned = !!localStorage.getItem(PIN_KEY);
    const collapsed = !!localStorage.getItem(COLLAPSE_KEY);
    if (pinned) setPinned(true);
    if (collapsed) setCollapsed(true);

    pinBtn.addEventListener('click', function (ev) {
      ev.preventDefault();
      const pressed = pinBtn.getAttribute('aria-pressed') === 'true';
      setPinned(!pressed);
    });

    // Double-click on pin toggles collapsed state (shortcut)
    pinBtn.addEventListener('dblclick', function (ev) {
      ev.preventDefault();
      const isCollapsed = document.documentElement.classList.contains('sidebar-collapsed');
      setCollapsed(!isCollapsed);
    });

    // Hover behavior: when not pinned, hovering over the mini-strip expands the sidebar
    const mini = document.getElementById('hawwa-mini-strip');
    const left = document.getElementById('left-sidebar');
    if (mini && left) {
      mini.addEventListener('mouseenter', function () { if (!document.documentElement.classList.contains('hawwa-sidebar-pinned')) { document.documentElement.classList.remove('hawwa-sidebar-hidden'); } });
      mini.addEventListener('mouseleave', function () { if (!document.documentElement.classList.contains('hawwa-sidebar-pinned')) { document.documentElement.classList.add('hawwa-sidebar-hidden'); } });
    }

    // Provide keyboard shortcut: Alt+\ to toggle collapse
    document.addEventListener('keydown', function (ev) {
      if (ev.altKey && ev.key === '\\') {
        const isCollapsed = document.documentElement.classList.contains('sidebar-collapsed');
        setCollapsed(!isCollapsed);
      }
    });

    // When screen resizes below large, remove pinned/hidden states
    window.addEventListener('resize', function () {
      if (window.innerWidth < 992) {
        ROOT.classList.remove('hawwa-sidebar-pinned', 'hawwa-sidebar-hidden', 'sidebar-collapsed');
      } else {
        // restore collapsed state if set
        if (localStorage.getItem(COLLAPSE_KEY)) ROOT.classList.add('sidebar-collapsed');
        if (localStorage.getItem(PIN_KEY)) ROOT.classList.add('hawwa-sidebar-pinned');
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
