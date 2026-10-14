"""Fake Tamil Nadu citizens. Common names only, no public figures. Father's name is the initial."""
import random
from dataclasses import dataclass, field
from datetime import date, timedelta

GIVEN_M = ["KARTHIK", "ARUN", "SURESH", "PRAKASH", "VIGNESH", "SENTHIL", "MANOJ", "DINESH", "GOKUL", "HARISH",
           "BALAJI", "SATHISH", "MURUGAN", "SARAVANAN", "RAJESH", "ASHOK", "KUMARAN", "NAVEEN", "PRAVEEN", "SIVA",
           "VIJAY", "ANAND", "GANESH", "MOHAN", "RAMESH", "SELVAM", "THIRU", "KANNAN", "BHARATH", "DEEPAK"]
GIVEN_F = ["MEENA", "PRIYA", "DIVYA", "KAVITHA", "LAKSHMI", "REVATHI", "SANGEETHA", "DEEPA", "ANITHA", "BHUVANA",
           "GAYATHRI", "HEMA", "JANANI", "KALAIVANI", "MALATHI", "NANDHINI", "PAVITHRA", "RADHA", "SATHYA", "SUDHA",
           "SWATHI", "UMA", "VANITHA", "YAMUNA", "ABIRAMI", "DHIVYA", "INDHU", "KEERTHANA", "MAHALAKSHMI", "SOWMYA"]
FATHERS = ["RAJENDRAN", "RAMESH", "SUBRAMANIAN", "KRISHNAN", "MURUGESAN", "PALANISAMY", "SHANMUGAM", "VELUSAMY",
           "GOVINDARAJ", "ARUMUGAM", "CHINNASAMY", "DURAISAMY", "ELANGOVAN", "GANESAN", "JAYARAMAN", "KANDASAMY",
           "LOGANATHAN", "MANICKAM", "NATARAJAN", "PERUMAL", "RAMASAMY", "SELVARAJ", "THANGARAJ", "VENKATESAN",
           "ANBALAGAN", "BALASUBRAMANIAM", "CHANDRASEKAR", "DHANDAPANI", "EASWARAN", "GOPAL", "ILANGO",
           "KALIAPPAN", "MAHALINGAM", "NAGARAJAN", "PALANIAPPAN", "RAJAGOPAL", "SAMIAPPAN", "SUNDARAM",
           "THIRUMALAI", "VADIVEL", "ANNADURAI", "BOOPATHI", "DEVARAJ", "GURUSAMY", "JEGANATHAN", "KARUPPUSAMY",
           "MARIMUTHU", "NALLASAMY", "PONNUSAMY", "RANGASAMY", "SAKTHIVEL", "SIVAKUMAR", "THANGAVEL", "VELMURUGAN",
           "ARJUNAN", "BALAKRISHNAN", "CHELLAPPAN", "DAMODARAN", "GNANASEKAR", "KUPPUSAMY"]
STREETS = ["GANDHI STREET", "NEHRU NAGAR", "KAMARAJ ROAD", "BHARATHI STREET", "TEMPLE STREET", "MAIN ROAD",
           "VOC STREET", "PERIYAR NAGAR", "ANNA NAGAR", "MARIAMMAN KOVIL STREET", "RAILWAY FEEDER ROAD"]
PLACES = [("SULUR", "641402"), ("PEELAMEDU", "641004"), ("GANDHIPURAM", "641012"), ("PODANUR", "641023"),
          ("PERUR", "641010"), ("MADUKKARAI", "641105"), ("ANNUR", "641653"), ("METTUPALAYAM", "641301"),
          ("POLLACHI", "642001"), ("KINATHUKADAVU", "642109"), ("ANAIMALAI", "642104"), ("VALPARAI", "642127"),
          ("SARAVANAMPATTI", "641035"), ("SINGANALLUR", "641005"), ("VADAVALLI", "641041")]


@dataclass
class Person:
    given: str
    father: str
    gender: str  # M | F
    dob: date
    house: str
    street: str
    place: str
    pin: str
    extra: dict = field(default_factory=dict)

    # Tamil Nadu naming styles (the father's name is the initial)
    @property
    def initial_first(self) -> str:
        return f"{self.father[0]}. {self.given}"

    @property
    def initial_last(self) -> str:
        return f"{self.given} {self.father[0]}"

    @property
    def full(self) -> str:
        return f"{self.given} {self.father}"

    def name_style(self, style: str) -> str:
        return {"initial_first": self.initial_first, "initial_last": self.initial_last, "full": self.full}[style]

    @property
    def relation(self) -> str:
        return "S/O" if self.gender == "M" else "D/O"

    def address_lines(self) -> list[str]:
        return [f"{self.relation} {self.father}, {self.house}, {self.street}", f"{self.place}, COIMBATORE",
                f"TAMIL NADU - {self.pin}"]


def random_dob(rng: random.Random) -> date:
    start, end = date(1950, 1, 1), date(2006, 12, 31)
    return start + timedelta(days=rng.randint(0, (end - start).days))


def make_person(rng: random.Random, gender: str | None = None) -> Person:
    gender = gender or rng.choice("MF")
    given = rng.choice(GIVEN_M if gender == "M" else GIVEN_F)
    place, pin = rng.choice(PLACES)
    return Person(given=given, father=rng.choice(FATHERS), gender=gender, dob=random_dob(rng),
                  house=str(rng.randint(1, 240)), street=rng.choice(STREETS), place=place, pin=pin)
