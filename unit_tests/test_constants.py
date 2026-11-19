"""Unit tests for the constants module."""

from ia700_project import constants


def test_planned_constant():
    """Test the planned column name."""
    assert constants.PLANNED == "Nombre de circulations prévues"


def test_cancelled_constant():
    """Test the cancelled column name."""
    assert constants.CANCELLED == "Nombre de trains annulés"


def test_delay_constant():
    """Test the delay column name."""
    assert constants.DELAY == "Retard moyen de tous les trains à l'arrivée"


def test_departure_constant():
    """Test the departure column name."""
    assert constants.DEPARTURE == "Gare de départ"


def test_arrival_constant():
    """Test the arrival column name."""
    assert constants.ARRIVAL == "Gare d'arrivée"
