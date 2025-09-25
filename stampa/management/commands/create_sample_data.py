from django.core.management.base import BaseCommand
from stampa.models import Categoria, Prodotto

class Command(BaseCommand):
    help = "Crea categorie e prodotti di esempio"

    def handle(self, *args, **options):
        items = {
            "Bovino": [
                ("Arrosto", "500g"),
                ("Bistecche", "500g"),
                ("Hamburger", "400g"),
                ("Straccetti", "500g"),
                ("Cotolette", "500g"),
                ("Macinato per polpette", "400g"),
            ],
            "Suino": [
                ("Braciole", "300g"),
            ],
            "Pollo": [
                ("Petto", "300g"),
            ],
        }
        for cat_name, products in items.items():
            cat, _ = Categoria.objects.get_or_create(nome=cat_name)
            for nome, peso in products:
                Prodotto.objects.get_or_create(categoria=cat, nome=nome, peso_default=peso)
        self.stdout.write(self.style.SUCCESS("Dati di esempio creati."))
