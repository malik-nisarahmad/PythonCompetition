document.getElementById('act').addEventListener('click', async () => {
  const out = document.getElementById('output');
  out.textContent = 'Today: ' + new Date().toLocaleString();
});
