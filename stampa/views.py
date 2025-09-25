from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.staticfiles import finders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from .models import Prodotto
from .forms import EtichettaBaseForm, ProdottoForm
import datetime
import json

def index(request):
    # Leggi prodotti + categoria
    prodotti = Prodotto.objects.select_related('categoria').order_by('categoria__nome', 'nome')

    # Prepara una lista "pulita" per il JS (JSON-serializable)
    products_json = [
        {
            "id": p.id,
            "nome": p.nome,
            "peso": p.peso_default or "",
            "categoria": p.categoria.nome
        }
        for p in prodotti
    ]
    categories = sorted({p["categoria"] for p in products_json})

    if request.method == "POST" and "aggiungi_prodotto" in request.POST:
        form_prod = ProdottoForm(request.POST)
        if form_prod.is_valid():
            form_prod.save()
            return redirect("index")
    else:
        form_prod = ProdottoForm()

    # Passiamo al template come JSON (stringhe)
    return render(request, "stampa/index.html", {
        "products": json.dumps(products_json),
        "categories": json.dumps(categories),
        "form": EtichettaBaseForm(),
        "prodotti": prodotti.order_by("categoria__nome", "nome"),
        "form_prod": form_prod,
    })


def elimina_prodotto(request, pk):
    prodotto = get_object_or_404(Prodotto, pk=pk)
    prodotto.delete()
    return redirect("index")


def print_pdf(request):
    if request.method != "POST":
        return redirect('index')

    form = EtichettaBaseForm(request.POST)
    if not form.is_valid():
        return redirect('index')

    data_scad = form.cleaned_data['data_scadenza']
    codice = form.cleaned_data['codice_animale']

    # raccogli tutte le etichette richieste
    prodotti_db = {p.id: p for p in Prodotto.objects.select_related('categoria').all()}
    etichette = []
    for key, value in request.POST.items():
        if key.startswith("qta_"):
            try:
                pid = int(key.split("_", 1)[1])
            except:
                continue
            try:
                qta = int(value) if value else 0
            except:
                qta = 0
            if qta > 0 and pid in prodotti_db:
                peso_custom = request.POST.get(f"peso_{pid}", prodotti_db[pid].peso_default or "")
                for _ in range(qta):
                    p = prodotti_db[pid]
                    etichette.append({
                        "nome": p.nome,
                        "peso": peso_custom or (p.peso_default or ""),
                        "categoria": p.categoria.nome,
                    })

    # Prepara PDF risposta
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="etichette.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    page_w, page_h = A4  # in points

    label_w = 105 * mm
    label_h = 48 * mm

    labels_per_row = 2
    rows_per_page = 6
    labels_per_page = labels_per_row * rows_per_page

    top_margin = (page_h - rows_per_page * label_h) / 2.0
    left_margin = (page_w - labels_per_row * label_w) / 2.0

    logo_path = finders.find('stampa/logo.png')  # metti il logo in static/stampa/logo.png

    def draw_one_label(cnv, x, y, item):
        # x,y = bottom-left del riquadro dell'etichetta
        margin_inner = 5 * mm
        if logo_path:
            try:
                cnv.drawImage(
                    logo_path,
                    x + margin_inner,
                    y + (label_h - 24*mm)/2,
                    width=24*mm,
                    height=24*mm,
                    preserveAspectRatio=True,
                    anchor='sw'
                )
            except Exception:
                pass

        text_x = x + margin_inner + 24*mm + 4*mm
        top_y = y + label_h

        cnv.setFont("Helvetica-Bold", 8)
        cnv.drawString(text_x, top_y - 6*mm, "LMG SOCIETA' AGRICOLA BENEFIT SRL")
        cnv.setFont("Helvetica", 7)
        cnv.drawString(text_x, top_y - 10*mm, "Via Boschi n. 2 Loc. Trasasso 40036 Monzuno (BO)")
        cnv.setFont("Helvetica", 6.5)
        cnv.drawString(text_x, top_y - 14*mm, "Regolamento CE n. 1760/2000 - Registrazione n. 2469 del 04/08/09")

        # categoria e codice solo se presenti
        if (item.get("categoria") or "").strip():
            cnv.drawString(text_x, top_y - 18*mm, f"{item['categoria'].upper()} N. {codice}")

        cnv.drawString(text_x, top_y - 22*mm, "CODICE MACELLO CEITB334G")

        if (item.get("nome") or "").strip():
            cnv.setFont("Helvetica-Bold", 10)
            cnv.drawString(text_x, top_y - 28*mm, item['nome'])
            cnv.setFont("Helvetica", 7.5)
            if item.get('peso'):
                cnv.drawString(text_x, top_y - 32*mm, f"PESO ALL'ORIGINE: {item['peso']}")

        cnv.setFont("Helvetica", 7)
        cnv.drawString(text_x, y + 12*mm, "DA CONSUMARE SOLO PREVIO COTTURA")

        # ✅ SCADENZA solo se non è un’etichetta vuota
        if (item.get("nome") or "").strip():
            scad_str = data_scad.strftime("%d/%m/%Y") if isinstance(data_scad, (datetime.date, datetime.datetime)) else str(data_scad)
            cnv.drawString(text_x, y + 7*mm, f"SCADENZA: {scad_str}")

        cnv.drawString(text_x, y + 3*mm, "Conservare: 0° - 4° C")

    # Itera etichette reali
    for idx, item in enumerate(etichette):
        pos_in_page = idx % labels_per_page
        if pos_in_page == 0 and idx != 0:
            c.showPage()
        col = pos_in_page % labels_per_row
        row = pos_in_page // labels_per_row
        label_x = left_margin + col * label_w
        label_y = page_h - top_margin - (row + 1) * label_h
        draw_one_label(c, label_x, label_y, item)

    # Riempimento con etichette vuote
    remainder = len(etichette) % labels_per_page
    if remainder != 0:
        for i in range(remainder, labels_per_page):
            col = i % labels_per_row
            row = i // labels_per_row
            label_x = left_margin + col * label_w
            label_y = page_h - top_margin - (row + 1) * label_h
            draw_one_label(c, label_x, label_y, {
                "nome": "",
                "peso": "",
                "categoria": ""
            })

    c.save()
    return response

