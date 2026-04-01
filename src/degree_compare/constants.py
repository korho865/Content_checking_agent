from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    critical: bool = False


FIELD_SPECS: Final[list[FieldSpec]] = [
    FieldSpec("opetustapa", "Opetustapa"),
    FieldSpec("opetusaika", "Opetusaika"),
    FieldSpec("maksullisuus", "Maksullisuus", critical=True),
    FieldSpec("koulutustyyppi", "Koulutustyyppi"),
    FieldSpec("suunnitelmankesto", "Suunnitelmankesto"),
    FieldSpec("opetuskieli", "Opetuskieli", critical=True),
    FieldSpec("koulutuksen_laajuus", "Koulutuksen laajuus", critical=True),
    FieldSpec("opetussuunnitelma", "Opetussuunnitelma", critical=True),
    FieldSpec("koulutuksen_kuvaus", "Koulutuksen kuvaus"),
]

FIELD_ORDER: Final[list[str]] = [spec.key for spec in FIELD_SPECS]

CRITICAL_FIELDS: Final[set[str]] = {spec.key for spec in FIELD_SPECS if spec.critical}
