import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from framework.models import Event
from framework.publication.smtp import SMTPAdapter


@pytest.fixture
def adapter():
    return SMTPAdapter(
        host="smtp.gmail.com",
        port=587,
        user="test@gmail.com",
        password="password",
        from_addr="test@gmail.com",
        to_addr="dest@gmail.com",
        summary=False,
    )


@pytest.fixture
def adapter_summary():
    return SMTPAdapter(
        host="smtp.gmail.com",
        port=587,
        user="test@gmail.com",
        password="password",
        from_addr="test@gmail.com",
        to_addr="dest@gmail.com",
        summary=True,
    )


@pytest.fixture
def eventos():
    now = datetime.now()
    return [
        Event(id=1, type_="race", name="10K Vigo", url="https://ex.gal",
              source="fga", event_date=now,
              data={"location": "Vigo", "distance": "10K"}),
        Event(id=2, type_="race", name="5K Baiona", url="https://ex.gal",
              source="fga", event_date=now,
              data={"location": "Baiona"}),
    ]


def test_send_individual_llama_smtp_por_evento(adapter, eventos):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        adapter.send(eventos)
        assert mock_server.sendmail.call_count == 2


def test_send_summary_llama_smtp_una_vez(adapter_summary, eventos):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        adapter_summary.send(eventos)
        assert mock_server.sendmail.call_count == 1


def test_send_lista_vacia_no_llama_smtp(adapter):
    with patch("smtplib.SMTP") as mock_smtp:
        adapter.send([])
        mock_smtp.assert_not_called()


def test_format_single_incluye_campos(adapter, eventos):
    result = adapter._format_single(eventos[0])
    assert "10K Vigo" in result
    assert "Vigo" in result
    assert "https://ex.gal" in result


def test_summary_subject_incluye_cantidad(adapter_summary, eventos):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        adapter_summary.send(eventos)
        call_args = mock_server.sendmail.call_args[0]
        assert "2" in call_args[2]