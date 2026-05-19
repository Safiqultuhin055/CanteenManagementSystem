/**
 * Thermal POS slip (80mm). Requires escapeHtml() and lastReceipt on the POS page.
 */
var RECEIPT_PAPER_MM = 80;

function receiptPrintCss() {
    var w = RECEIPT_PAPER_MM + 'mm';
    var px = Math.round(RECEIPT_PAPER_MM / 25.4 * 96);
    return {
        windowFeatures: 'width=' + px + ',height=720,menubar=no,toolbar=no,location=no,status=no',
        css:
            '@page { size: ' + w + ' auto; margin: 0; }' +
            'html { width: ' + w + '; max-width: ' + w + '; margin: 0; padding: 0; }' +
            'body { width: ' + w + '; max-width: ' + w + '; margin: 0; padding: 3mm 2mm 4mm; ' +
            'font-family: "Courier New", Courier, monospace; font-size: 11px; line-height: 1.3; color: #000; background: #fff; }' +
            '.receipt { width: 100%; }' +
            '.c { text-align: center; }' +
            '.shop { font-size: 13px; font-weight: bold; text-transform: uppercase; margin-bottom: 2px; }' +
            '.addr { font-size: 9px; text-align: center; margin-bottom: 1px; }' +
            '.title { font-size: 12px; font-weight: bold; margin: 4px 0; letter-spacing: 0.06em; }' +
            '.div { text-align: center; font-size: 10px; margin: 3px 0; line-height: 1; white-space: nowrap; overflow: hidden; }' +
            '.items-hdr, .item-row { display: grid; gap: 2px 4px; align-items: start; }' +
            '.customer-slip .items-hdr, .customer-slip .item-row { grid-template-columns: 8mm 1fr 12mm; }' +
            '.kitchen-slip .items-hdr, .kitchen-slip .item-row { grid-template-columns: 9mm 1fr; }' +
            '.items-hdr { font-size: 9px; font-weight: bold; margin: 5px 0 3px; border-bottom: 1px dashed #000; padding-bottom: 2px; }' +
            '.items-hdr span:last-child, .item-row .amt { text-align: right; }' +
            '.item-row { font-size: 11px; padding: 2px 0; }' +
            '.item-row .item { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }' +
            '.qty { text-align: center; font-weight: bold; }' +
            '.total-row { display: flex; justify-content: space-between; font-size: 15px; font-weight: bold; margin: 5px 0 3px; }' +
            '.pay { font-size: 10px; margin: 2px 0 4px; }' +
            '.pay-row, .meta .row { display: flex; justify-content: space-between; gap: 4px; font-size: 9px; }' +
            '.token { font-size: 20px; font-weight: bold; text-align: center; margin: 6px 0; }' +
            '.kitchen-slip .token { font-size: 24px; }' +
            '.meta { margin: 4px 0; }' +
            '.thanks { font-size: 12px; font-weight: bold; text-align: center; margin: 8px 0 4px; }' +
            '.kitchen-note { font-size: 11px; font-weight: bold; text-align: center; margin: 6px 0; }' +
            '.bc-wrap { text-align: center; margin-top: 6px; }' +
            '#barcode { max-width: 100%; height: 44px; }' +
            '@media print {' +
            '  html, body { width: ' + w + ' !important; max-width: ' + w + ' !important; min-width: ' + w + ' !important; ' +
            '    margin: 0 !important; padding: 2mm !important; height: auto !important; }' +
            '  body { position: absolute; left: 0; top: 0; }' +
            '}'
    };
}

function buildReceiptHtml(r, slipType) {
    slipType = slipType || 'customer';
    var isKitchen = slipType === 'kitchen';
    var divider = '<div class="div">*******************************</div>';
    var payLabel = (r.payment_method || 'Cash').toLowerCase() === 'card' ? 'Card' : 'Cash';
    var barcodeVal = String(r.barcode || r.order_number || r.token_number).replace(/[^\x20-\x7E]/g, '');
    var barcodeJson = JSON.stringify(barcodeVal);
    var footerMsg = String(r.footer_text || 'THANK YOU!').toUpperCase();
    var style = receiptPrintCss();

    var itemLines = (r.items || []).map(function(item) {
        var qty = item.qty || 1;
        var name = item.name || '';
        if (name.length > 20) name = name.slice(0, 18) + '..';
        var qtyStr = String(qty);
        if (isKitchen) {
            return '<div class="item-row"><span class="qty">' + qtyStr + '</span><span class="item">' + escapeHtml(name) + '</span></div>';
        }
        var price = parseFloat(item.line_total).toFixed(1);
        return '<div class="item-row"><span class="qty">' + qtyStr + '</span><span class="item">' + escapeHtml(name) + '</span><span class="amt">' + price + '</span></div>';
    }).join('');

    var total = parseFloat(r.total_amount).toFixed(1);
    var tax = parseFloat(r.tax_amount || 0);
    var taxRow = !isKitchen && tax > 0
        ? '<div class="pay-row"><span>Tax</span><span>' + tax.toFixed(1) + '</span></div>'
        : '';
    var bodyClass = isKitchen ? 'kitchen-slip' : 'customer-slip';
    var title = isKitchen ? 'KITCHEN ORDER' : 'CASH RECEIPT';

    var body = '<div class="receipt ' + bodyClass + '">';
    body += '<div class="c shop">' + escapeHtml(r.business_name || 'Canteen') + '</div>';
    if (!isKitchen) {
        if (r.business_address) body += '<div class="addr">' + escapeHtml(r.business_address) + '</div>';
        if (r.business_phone) body += '<div class="addr">Tel: ' + escapeHtml(r.business_phone) + '</div>';
    }
    body += divider;
    body += '<div class="c title">' + title + '</div>';
    body += divider;

    if (isKitchen) {
        body += '<div class="c token">TOKEN #' + escapeHtml(String(r.token_number)) + '</div>';
        body += '<div class="meta"><div class="row"><span>Order</span><span>' + escapeHtml(r.order_number) + '</span></div>';
        body += '<div class="row"><span>Time</span><span>' + escapeHtml(r.order_time) + '</span></div></div>';
        body += divider;
        body += '<div class="items-hdr"><span>QTY</span><span>ITEM</span></div>';
        body += itemLines;
        body += divider;
        body += '<div class="c kitchen-note">Prepare for pickup</div>';
    } else {
        body += '<div class="items-hdr"><span>QTY</span><span>ITEM</span><span>AMT</span></div>';
        body += itemLines;
        body += divider;
        body += '<div class="total-row"><span>Total</span><span>' + total + '</span></div>';
        body += '<div class="pay"><div class="pay-row"><span>' + escapeHtml(payLabel) + '</span><span>' + total + '</span></div>' + taxRow + '</div>';
        body += divider;
        body += '<div class="c token">Token #' + escapeHtml(String(r.token_number)) + '</div>';
        body += '<div class="meta">';
        body += '<div class="row"><span>Order</span><span>' + escapeHtml(r.order_number) + '</span></div>';
        body += '<div class="row"><span>Date</span><span>' + escapeHtml(r.order_time) + '</span></div>';
        body += '<div class="row"><span>Customer</span><span>' + escapeHtml(r.customer_name) + '</span></div>';
        body += '<div class="row"><span>Cashier</span><span>' + escapeHtml(r.cashier || '-') + '</span></div>';
        body += '</div>';
        body += divider;
        body += '<div class="c thanks">' + escapeHtml(footerMsg) + '</div>';
        body += '<div class="bc-wrap"><svg id="barcode"></svg></div>';
    }
    body += '</div>';

    var printScript = isKitchen
        ? '<script>window.onafterprint=function(){try{window.close();}catch(e){}};setTimeout(function(){window.focus();window.print();},120);<\/script>'
        : '<script>(function(){var v=' + barcodeJson + ';window.onafterprint=function(){try{window.close();}catch(e){}};function go(){try{if(window.JsBarcode){JsBarcode("#barcode",v,{format:"CODE128",width:1.5,height:40,displayValue:true,fontSize:10,margin:2});}}catch(e){}window.focus();window.print();}setTimeout(go,180);})();<\/script>';

    return '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Receipt</title>' +
        '<style>' + style.css + '</style>' +
        (!isKitchen ? '<script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js"><\/script>' : '') +
        '</head><body class="' + bodyClass + '">' + body + printScript + '</body></html>';
}

function printReceiptHtml(html) {
    var style = receiptPrintCss();
    var w = window.open('', 'cms_receipt_print', style.windowFeatures);
    if (w) {
        w.document.open();
        w.document.write(html);
        w.document.close();
        return;
    }
    var frame = document.createElement('iframe');
    frame.style.cssText = 'position:fixed;left:0;top:0;width:' + RECEIPT_PAPER_MM + 'mm;height:90vh;border:0;z-index:99999;background:#fff';
    document.body.appendChild(frame);
    frame.contentWindow.document.open();
    frame.contentWindow.document.write(html);
    frame.contentWindow.document.close();
    setTimeout(function() {
        try {
            frame.contentWindow.focus();
            frame.contentWindow.print();
        } catch (e) { /* blocked */ }
        setTimeout(function() { frame.remove(); }, 15000);
    }, 200);
}

function printReceipt(receipt, options) {
    if (!receipt) return;
    options = options || {};
    lastReceipt = receipt;

    var slips = [];
    if (options.kitchenOnly) {
        slips.push('kitchen');
    } else if (options.customerOnly) {
        slips.push('customer');
    } else {
        slips.push('customer');
        if (options.printKitchen === true) slips.push('kitchen');
    }

    slips.forEach(function(type, i) {
        setTimeout(function() {
            printReceiptHtml(buildReceiptHtml(receipt, type));
        }, i * 3200);
    });
}

function reprintLastReceipt() {
    if (lastReceipt) printReceipt(lastReceipt, { customerOnly: true });
    else showToast('No receipt to print', 'error');
}

function reprintKitchenSlip() {
    if (lastReceipt) printReceipt(lastReceipt, { kitchenOnly: true });
    else showToast('No receipt to print', 'error');
}
