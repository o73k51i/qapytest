"""Module to test handling of different languages and Unicode payloads."""

import pytest

from qapytest import soft_assert, step


@pytest.mark.parametrize(
    "payload",
    [
        {"input": "English text", "language": "English"},
        {"input": "Український текст", "language": "Ukrainian"},
        {"input": "النص العربي", "language": "Arabic"},
        {"input": "中文测试", "language": "Chinese"},
        {"input": "日本語テスト", "language": "Japanese"},
        {"input": "한국어 테스트", "language": "Korean"},
        {"input": "Texto en español", "language": "Spanish"},
        {"input": "Texte français", "language": "French"},
        {"input": "Deutscher Text", "language": "German"},
    ],
    ids=["english", "український", "العربي", "中文", "日本語", "한국어", "español", "français", "deutsch"],
)
@pytest.mark.title("Test with different languages ​​and Unicode loads")
def test_multilingual(payload: dict) -> None:
    """Test handling of different languages and Unicode payloads."""
    language_map = {
        "English": "Logging payload for {}: {}",
        "Ukrainian": "Логування корисного навантаження для {}: {}",
        "Arabic": "تسجيل البيانات لـ {}: {}",
        "Chinese": "为 {} 记录负载: {}",
        "Japanese": "{}のペイロードをログ記録: {}",
        "Korean": "{}에 대한 페이로드 로깅: {}",
        "Spanish": "Registrando carga útil para {}: {}",
        "French": "Enregistrement de la charge utile pour {} : {}",
        "German": "Protokollierung der Nutzlast für {}: {}",
    }

    assertion_map = {
        "English": "This soft assertion should pass for {}",
        "Ukrainian": "Це м'яке твердження повинно пройти для {}",
        "Arabic": "يجب أن يمر هذا التأكيد المرن لـ {}",
        "Chinese": "这个软断言应该通过 {}",
        "Japanese": "このソフトアサーションは{}について成功するはずです",
        "Korean": "이 소프트 어설션은 {}에 대해 통과해야 합니다",
        "Spanish": "Esta aserción suave debería pasar para {}",
        "French": "Cette assertion souple devrait réussir pour {}",
        "German": "Diese weiche Assertion sollte für {} bestehen",
    }

    language = payload["language"]
    step_msg = language_map[language].format(language, payload["input"])
    assertion_msg = assertion_map[language].format(language)

    with step(step_msg):
        soft_assert(True, assertion_msg)
