(() => {
  document.querySelectorAll('.metric-info').forEach((wrapper) => {
    const button = wrapper.querySelector('button');
    const panel = wrapper.querySelector('.metric-info-panel');
    let pinned = false;
    let timer;
    const position = () => {
      if (panel.hidden) return;
      const anchor = button.getBoundingClientRect();
      const box = panel.getBoundingClientRect();
      const left = Math.max(12, Math.min(anchor.right - box.width, window.innerWidth - box.width - 12));
      const below = anchor.bottom + 8;
      const top = below + box.height <= window.innerHeight - 12 ? below : Math.max(12, anchor.top - box.height - 8);
      panel.style.left = `${left}px`;
      panel.style.top = `${top}px`;
    };
    const show = () => {
      clearTimeout(timer);
      panel.hidden = false;
      button.setAttribute('aria-expanded', 'true');
      position();
    };
    const hide = () => {
      clearTimeout(timer);
      pinned = false;
      panel.hidden = true;
      button.setAttribute('aria-expanded', 'false');
    };
    [button, panel].forEach((element) => {
      element.addEventListener('pointerenter', (event) => {
        if (event.pointerType === 'mouse') show();
      });
      element.addEventListener('pointerleave', () => {
        timer = setTimeout(() => {
          if (!pinned && !wrapper.contains(document.activeElement)) hide();
        }, 180);
      });
    });
    button.addEventListener('click', () => {
      if (pinned) hide();
      else { pinned = true; show(); }
    });
    wrapper.addEventListener('focusin', show);
    wrapper.addEventListener('focusout', (event) => {
      if (!wrapper.contains(event.relatedTarget)) hide();
    });
    document.addEventListener('pointerdown', (event) => {
      if (!wrapper.contains(event.target)) hide();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !panel.hidden) {
        if (panel.contains(document.activeElement)) button.focus();
        hide();
      }
    });
    window.addEventListener('resize', position);
    window.addEventListener('scroll', position, true);
  });
})();
