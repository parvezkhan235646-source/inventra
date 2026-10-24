(() => {
  const form = document.getElementById("billing-form");
  if (!form) return;

  const rows = document.getElementById("product-rows");
  const search = document.getElementById("product-search");
  const addButton = form.querySelector(".add-row");
  const money = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  });
  const roundMoney = (amount) => Math.round((amount + Number.EPSILON) * 100) / 100;

  function applyProductFilter() {
    const query = search.value.trim().toLocaleLowerCase();
    rows.querySelectorAll('select[name="product_id[]"]').forEach((select) => {
      Array.from(select.options).forEach((option) => {
        if (!option.value) return;
        const matches = option.dataset.search.toLocaleLowerCase().includes(query);
        option.disabled = Boolean(query) && !matches && !option.selected;
      });
    });
  }

  function updateSummary() {
    let subtotal = 0;
    let itemCount = 0;

    rows.querySelectorAll(".bill-row").forEach((row) => {
      const select = row.querySelector('select[name="product_id[]"]');
      const quantityInput = row.querySelector('input[name="quantity[]"]');
      const selected = select.selectedOptions[0];
      const price = Number(selected?.dataset.price || 0);
      const stock = Number(selected?.dataset.stock || 0);
      const quantity = Math.max(0, Number.parseInt(quantityInput.value, 10) || 0);
      const lineTotal = roundMoney(price * quantity);
      const hasProduct = Boolean(select.value);

      row.querySelector(".bill-line-total").textContent = hasProduct
        ? money.format(lineTotal)
        : "—";
      row.querySelector(".bill-stock").textContent = hasProduct
        ? `${stock} available${quantity > stock ? " · exceeds stock" : ""}`
        : "Choose an item to see available stock";
      row.querySelector(".bill-stock").classList.toggle("stock-warning", hasProduct && quantity > stock);

      if (hasProduct) {
        subtotal += lineTotal;
        itemCount += quantity;
      }
    });

    const discountRate = Number.parseFloat(form.elements.discount.value) || 0;
    const taxRate = Number.parseFloat(form.elements.tax.value) || 0;
    subtotal = roundMoney(subtotal);
    const discount = roundMoney(subtotal * discountRate / 100);
    const taxableSubtotal = subtotal - discount;
    const tax = roundMoney(taxableSubtotal * taxRate / 100);
    const total = roundMoney(taxableSubtotal + tax);

    document.getElementById("summary-item-count").textContent =
      `${itemCount} ${itemCount === 1 ? "item" : "items"}`;
    document.getElementById("summary-subtotal").textContent = money.format(subtotal);
    document.getElementById("summary-discount").textContent = `− ${money.format(discount)}`;
    document.getElementById("summary-tax").textContent = money.format(tax);
    document.getElementById("summary-total").textContent = money.format(total);
  }

  function addRow() {
    const clone = rows.querySelector(".bill-row").cloneNode(true);
    const select = clone.querySelector('select[name="product_id[]"]');
    select.selectedIndex = 0;
    clone.querySelector('input[name="quantity[]"]').value = 1;
    clone.querySelector(".bill-stock").textContent = "Choose an item to see available stock";
    clone.querySelector(".bill-line-total").textContent = "—";
    rows.appendChild(clone);
    applyProductFilter();
    updateSummary();
    select.focus();
  }

  function removeRow(button) {
    const row = button.closest(".bill-row");
    if (rows.querySelectorAll(".bill-row").length === 1) {
      row.querySelector('select[name="product_id[]"]').selectedIndex = 0;
      row.querySelector('input[name="quantity[]"]').value = 1;
    } else {
      row.remove();
    }
    updateSummary();
  }

  addButton.addEventListener("click", addRow);
  search.addEventListener("input", applyProductFilter);
  form.addEventListener("input", updateSummary);
  form.addEventListener("change", updateSummary);
  rows.addEventListener("click", (event) => {
    const button = event.target.closest(".remove-row");
    if (button) removeRow(button);
  });
  updateSummary();
})();
