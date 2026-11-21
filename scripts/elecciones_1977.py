"""Candidaturas con escaño según el resumen de la Junta Electoral Central."""
from decimal import Decimal, ROUND_HALF_UP


SOURCE = "https://www.juntaelectoralcentral.es/cs/jec/documentos/GENERALES_1977_Resultados.pdf"
MINISTRY_SOURCE = "https://infoelectoral.interior.gob.es/es/elecciones-celebradas/area-de-descargas/index.html"
MINISTRY_UCD_VOTES = 6310391
EXAM_UCD_SEATS = 166
EXAM_OTHER_SEATS = 11

# La JEC presenta PSC-PSOE y PSUC por separado; aquí se agrupan con PSOE y PCE.
RESULTS = (
    ("UCD", "UCD — Unión de Centro Democrático", 6309517, 165),
    ("PSOE", "PSOE y PSC-PSOE", 4467745 + 870362, 103 + 15),
    ("PCE", "PCE y PSUC", 1150774 + 561132, 12 + 8),
    ("AP", "AP — Alianza Popular", 1471527, 16),
    ("PDC", "PDC — Pacte Democràtic per Catalunya", 514647, 11),
    ("PNV", "PNV — Partido Nacionalista Vasco", 296193, 8),
    ("PSP-US", "PSP-US — Partido Socialista Popular-Unidad Socialista", 816754, 6),
    ("UDC-CD", "UDC-CD — Unió del Centre i la Democràcia Cristiana de Catalunya", 172791, 2),
    ("EC-FED", "EC-FED — Esquerra de Catalunya", 143954, 1),
    ("EE", "EE — Euskadiko Ezkerra", 61417, 1),
    ("CIC", "Candidaturas independientes de centro", 67017, 2),
)


def seats_percent(seats):
    return str((Decimal(seats) * 100 / 350).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )).replace(".", ",")


def votes_text(votes):
    return f"{votes:,}".replace(",", " ")
