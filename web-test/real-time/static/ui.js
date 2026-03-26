document.addEventListener('DOMContentLoaded', () => {
  const modals = document.querySelectorAll('.modal');
  const overlay = document.getElementById('modal-overlay');
  const closeBtns = document.querySelectorAll('.modal-close');
  
  // Open modal logic
  document.querySelectorAll('[data-open-modal]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = btn.getAttribute('data-open-modal');
      const targetModal = document.getElementById(modalId);
      if (targetModal) {
        overlay.classList.add('active');
        targetModal.classList.add('active');
      }
    });
  });

  // Close logic
  const closeModal = () => {
    overlay.classList.remove('active');
    modals.forEach(m => m.classList.remove('active'));
  };

  closeBtns.forEach(btn => btn.addEventListener('click', closeModal));
  
  if (overlay) {
    overlay.addEventListener('click', closeModal);
  }

  // Prevent clicks inside modal from closing it
  modals.forEach(modal => {
    modal.addEventListener('click', (e) => {
      e.stopPropagation();
    });
  });
});
