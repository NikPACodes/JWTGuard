import pytest


@pytest.mark.django_db
def test_get_user_session_ids_returns_strings(token_store):
    """
    Тест корректного получения списка session IDs пользователя из Redis.

    Проверки:
    - возвращаются строки;
    - возвращаются все сохранённые SID.
    """
    token_store.redis_client.sadd("jwt:user_sessions:1", "sid-1", "sid-2")
    result = token_store.get_user_session_ids(user_id=1)
    assert sorted(result) == ["sid-1", "sid-2"]


@pytest.mark.django_db
def test_refresh_whitelist_lifecycle(token_store):
    """
    Тест lifecycle refresh whitelist.

    Проверки:
    - refresh корректно добавляется в whitelist;
    - refresh корректно удаляется из whitelist.
    """
    token_store.add_refresh_to_whitelist(
        jti='refresh-jti',
        user_id=1,
        session_id='sid-1',
        exp=300,
    )
    assert token_store.is_refresh_whitelisted(jti='refresh-jti')

    token_store.remove_refresh_from_whitelist(jti='refresh-jti')
    assert not token_store.is_refresh_whitelisted(jti='refresh-jti')


@pytest.mark.django_db
def test_blacklist_lifecycle(token_store):
    """
    Тест lifecycle token blacklist.

    Проверки:
    - token корректно добавляется в blacklist;
    - blacklist корректно определяется при проверке.
    """
    token_store.add_to_blacklist(
        jti='token-jti',
        exp=120,
        user_id=1,
        session_id="sid-1",
        token_type='test',
        reason='test',
    )
    assert token_store.is_blacklisted(jti='token-jti')


@pytest.mark.django_db
def test_session_lifecycle(token_store):
    """
    Тест lifecycle Redis session.

    Проверки:
    - session корректно создаётся;
    - session корректно читается;
    - session индексируется в user_sessions;
    - session корректно удаляется;
    - SID удаляется из user_sessions.
    """
    token_store.create_session(
        session_id='sid-1',
        user_id=1,
        access_jti='access-jti',
        access_exp=120,
        refresh_jti='refresh-jti',
        refresh_exp=300,
    )

    session = token_store.get_session(session_id='sid-1')
    assert session is not None
    assert session['access_jti'] == "access-jti"
    assert session['refresh_jti'] == "refresh-jti"

    user_session_ids = token_store.get_user_session_ids(user_id=1)
    assert "sid-1" in user_session_ids

    token_store.delete_session(session_id="sid-1")
    assert token_store.get_session(session_id="sid-1") is None
    assert "sid-1" not in token_store.get_user_session_ids(user_id=1)