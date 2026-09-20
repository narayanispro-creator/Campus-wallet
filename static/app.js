'use strict';
const $ = (selector) => document.querySelector(selector);
const money = (paise) => new Intl.NumberFormat('en-IN', {style: 'currency', currency: 'INR'}).format(paise / 100);
let dashboard = null, pendingDelete = null, loadVersion = 0;
const monthInput = $('#month');
const token = $('meta[name="csrf-token"]').content;
function message(text, error = false) { $('#status').textContent = text; $('#status').className = error ? 'error' : ''; }
async function api(path, method = 'GET', body) {
  const response = await fetch(path, {method, headers: {'Content-Type': 'application/json', 'X-CSRF-Token': token}, body: body ? JSON.stringify(body) : undefined});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
}
function el(tag, className, text) { const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node; }
async function load() {
  const version = ++loadVersion;
  try {
    const data = await api('/api/dashboard?month=' + encodeURIComponent(monthInput.value));
    if (version !== loadVersion) return;
    dashboard = data; render();
  } catch (error) { message(error.message, true); }
}
function render() {
  const d = dashboard;
  $('#total').textContent = money(d.total);
  $('#count').textContent = `${d.expenses.length} expense${d.expenses.length === 1 ? '' : 's'} this month`;
  $('#budget').textContent = d.budget === null ? 'Not set' : money(d.budget);
  $('#remaining').textContent = d.budget === null ? '—' : money(Math.abs(d.budget - d.total));
  $('#remaining').classList.toggle('over', d.budget !== null && d.total > d.budget);
  $('#remaining-label').textContent = d.budget !== null && d.total > d.budget ? 'OVER BUDGET' : 'LEFT TO SPEND';
  $('#budget-progress').style.width = d.budget ? `${Math.min(100, d.total / d.budget * 100)}%` : '0%';
  $('#budget-progress').style.background = d.budget && d.total > d.budget ? '#b33d36' : '#86aa5b';
  $('#budget-message').textContent = d.budget ? `${Math.round(d.total / d.budget * 100)}% of your monthly budget used` : 'Set a budget to track your balance';
  $('#transaction-count').textContent = d.expenses.length;
  const daily = $('#daily-chart'); daily.replaceChildren();
  const maximum = Math.max(...d.daily, 1);
  d.daily.forEach((value, i) => {
    const bar = el('button', 'bar' + (value ? '' : ' zero'));
    bar.type = 'button'; bar.style.height = `${Math.max(2, value / maximum * 100)}%`;
    bar.title = `Day ${i + 1}: ${money(value)}`; bar.setAttribute('aria-label', bar.title);
    bar.addEventListener('click', () => message(`${d.month}-${String(i+1).padStart(2,'0')}: ${money(value)} spent`)); daily.append(bar);
  });
  $('#last-day').textContent = d.daily.length; $('#mid-day').textContent = Math.ceil(d.daily.length / 2);
  const categories = $('#category-chart'); categories.replaceChildren();
  Object.entries(d.categories).sort((a,b) => b[1]-a[1]).forEach(([name, value]) => {
    const line = el('div', 'category-line'); line.append(el('span', '', name));
    const track = el('div', 'category-track'), fill = el('div', 'category-fill');
    fill.style.width = `${d.total ? value / d.total * 100 : 0}%`; track.append(fill);
    line.append(track, el('strong', '', money(value))); categories.append(line);
  });
  renderRows();
}
function renderRows() {
  if (!dashboard) return;
  const query = $('#search').value.trim().toLowerCase(), category = $('#filter-category').value;
  const rows = dashboard.expenses.filter(e => (!category || e.category === category) && `${e.title} ${e.notes}`.toLowerCase().includes(query));
  const tbody = $('#expense-rows'); tbody.replaceChildren();
  for (const expense of rows) {
    const tr = el('tr'), title = el('td', 'expense-title', expense.title);
    if (expense.notes) title.append(el('div', 'note', expense.notes));
    const categoryCell = el('td'); categoryCell.append(el('span', 'badge', expense.category));
    tr.append(title, categoryCell, el('td', '', new Date(expense.spent_on + 'T12:00:00').toLocaleDateString('en-IN', {day:'numeric',month:'short',year:'numeric'})), el('td','amount',money(expense.amount)));
    const actions = el('td', 'actions'), edit = el('button','','Edit'), remove = el('button','','Delete');
    edit.setAttribute('aria-label',`Edit ${expense.title}`); remove.setAttribute('aria-label',`Delete ${expense.title}`);
    edit.addEventListener('click', () => openExpense(expense));
    remove.addEventListener('click', () => { pendingDelete = expense.id; $('#delete-description').textContent = `${expense.title} · ${money(expense.amount)}. This cannot be undone.`; $('#delete-form .form-error').textContent = ''; $('#delete-dialog').showModal(); });
    actions.append(edit,remove); tr.append(actions); tbody.append(tr);
  }
  $('#empty').hidden = rows.length > 0;
  $('#empty h3').textContent = dashboard.expenses.length ? 'No matches found' : 'A fresh start';
  $('#empty p').textContent = dashboard.expenses.length ? 'Try another search or category.' : 'Add your first expense to see your month take shape.';
  $('#filtered-summary').textContent = `${rows.length} of ${dashboard.expenses.length} expenses · ${money(rows.reduce((sum,e) => sum + e.amount,0))} shown`;
}
function openExpense(expense) {
  const form = $('#expense-form'); form.reset(); form.querySelector('.form-error').textContent = '';
  $('#form-title').textContent = expense ? 'Edit expense' : 'Add expense';
  for (const name of ['id','title','category','spent_on','notes']) if (expense) form.elements[name].value = expense[name];
  if (expense) form.elements.amount.value = (expense.amount/100).toFixed(2);
  else form.elements.spent_on.value = monthInput.value === document.body.dataset.today.slice(0,7) ? document.body.dataset.today : monthInput.value + '-01';
  $('#expense-dialog').showModal();
}
async function submit(form, action) {
  const button = form.querySelector('[type="submit"]'); button.disabled = true; form.querySelector('.form-error').textContent = '';
  try { await action(); form.closest('dialog').close(); await load(); }
  catch (error) { form.querySelector('.form-error').textContent = error.message; }
  finally { button.disabled = false; }
}
$('#add-expense').addEventListener('click', () => openExpense());
$('#edit-budget').addEventListener('click', () => {
  if (!dashboard || dashboard.month !== monthInput.value) return message('Wait for the selected month to load.', true);
  $('#budget-form').reset(); $('#budget-form .form-error').textContent = '';
  $('#budget-period').textContent = `Plan your spending for ${monthInput.value}.`;
  $('#budget-form').elements.amount.value = dashboard.budget ? (dashboard.budget/100).toFixed(2) : '';
  $('#budget-dialog').showModal();
});
$('#expense-form').addEventListener('submit', event => {
  event.preventDefault(); const form = event.currentTarget, data = Object.fromEntries(new FormData(form));
  submit(form, async () => { await api(data.id ? `/api/expenses/${data.id}` : '/api/expenses', data.id ? 'PUT' : 'POST', data); monthInput.value = data.spent_on.slice(0,7); message(data.id ? 'Expense updated.' : 'Expense added.'); });
});
$('#budget-form').addEventListener('submit', event => { event.preventDefault(); const form = event.currentTarget; submit(form, async () => { await api('/api/budget', 'PUT', {month:monthInput.value, amount:form.elements.amount.value}); message('Monthly budget saved.'); }); });
$('#delete-form').addEventListener('submit', event => { event.preventDefault(); submit(event.currentTarget, async () => { await api(`/api/expenses/${pendingDelete}`, 'DELETE'); message('Expense deleted.'); }); });
document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
monthInput.addEventListener('change', () => { if (!monthInput.value) { monthInput.value = dashboard ? dashboard.month : document.body.dataset.today.slice(0,7); return; } message(''); load(); });
$('#search').addEventListener('input', renderRows); $('#filter-category').addEventListener('change', renderRows);
load();
