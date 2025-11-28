// ChromeForge Generated Popup Script
document.addEventListener('DOMContentLoaded', function() {
  const actionBtn = document.getElementById('actionBtn');
  const output = document.getElementById('output');
  const status = document.getElementById('status');
  
  function updateDateTime() {
    const now = new Date();
    const options = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    };
    output.innerHTML = '<div class="date-display">' + now.toLocaleDateString('en-US', options) + '</div>';
  }
  
  updateDateTime();

  actionBtn.addEventListener('click', updateDateTime);
});
