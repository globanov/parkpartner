"""Tests for ParkPartner state management"""

import asyncio
from unittest.mock import MagicMock

import pytest

from app.core.state import (
    get_session_histories,
    get_session_lock,
    get_whisper_model,
    set_session_histories,
    set_whisper_model,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state after each test"""
    yield
    set_session_histories({})
    set_whisper_model(None)


class TestSessionHistories:
    """Test session histories management"""

    def test_get_session_histories_initial(self):
        """Test initial session histories is empty dict"""
        histories = get_session_histories()
        assert histories == {}
        assert isinstance(histories, dict)

    def test_set_session_histories(self):
        """Test setting session histories"""
        test_data = {
            "session1": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
            "session2": [
                {"role": "user", "content": "How are you?"},
            ],
        }

        set_session_histories(test_data)
        histories = get_session_histories()

        assert histories == test_data
        assert len(histories) == 2

    def test_set_session_histories_empty(self):
        """Test setting empty session histories"""
        set_session_histories({})
        histories = get_session_histories()
        assert histories == {}

    def test_session_histories_persistence(self):
        """Test that session histories persist across calls"""
        set_session_histories({"test": [{"role": "user", "content": "msg"}]})

        histories1 = get_session_histories()
        histories2 = get_session_histories()

        assert histories1 == histories2
        assert "test" in histories1

    def test_session_histories_mutable(self):
        """Test that session histories can be modified"""
        set_session_histories({})

        histories = get_session_histories()
        histories["new_session"] = [{"role": "user", "content": "test"}]

        # Verify modification persists
        assert "new_session" in get_session_histories()


class TestSessionLock:
    """Test session lock management"""

    def test_get_session_lock(self):
        """Test getting session lock"""
        lock = get_session_lock()
        assert isinstance(lock, asyncio.Lock)

    def test_session_lock_is_singleton(self):
        """Test that same lock is returned on each call"""
        lock1 = get_session_lock()
        lock2 = get_session_lock()
        assert lock1 is lock2

    @pytest.mark.asyncio
    async def test_session_lock_works(self):
        """Test that lock can be acquired and released"""
        lock = get_session_lock()

        async with lock:
            # Lock is held
            assert lock.locked()

        # Lock is released
        assert not lock.locked()

    @pytest.mark.asyncio
    async def test_session_lock_prevents_concurrent_access(self):
        """Test that lock prevents concurrent access"""
        lock = get_session_lock()
        execution_order = []

        async def task(task_id):
            async with lock:
                execution_order.append(f"{task_id}_start")
                await asyncio.sleep(0.01)
                execution_order.append(f"{task_id}_end")

        # Run multiple tasks concurrently
        await asyncio.gather(task(1), task(2), task(3))

        # Verify tasks executed sequentially (no interleaving)
        # Each task should start and end before next starts
        for i in range(0, len(execution_order), 2):
            assert execution_order[i].endswith("_start")
            assert execution_order[i + 1].endswith("_end")


class TestWhisperModel:
    """Test Whisper model management"""

    def test_get_whisper_model_initial(self):
        """Test initial Whisper model is None"""
        model = get_whisper_model()
        assert model is None

    def test_set_whisper_model(self):
        """Test setting Whisper model"""
        mock_model = MagicMock()
        set_whisper_model(mock_model)

        model = get_whisper_model()
        assert model is mock_model

    def test_set_whisper_model_none(self):
        """Test setting Whisper model to None"""
        mock_model = MagicMock()
        set_whisper_model(mock_model)
        set_whisper_model(None)

        model = get_whisper_model()
        assert model is None

    def test_whisper_model_persistence(self):
        """Test that Whisper model persists across calls"""
        mock_model = MagicMock(name="test_model")
        set_whisper_model(mock_model)

        model1 = get_whisper_model()
        model2 = get_whisper_model()

        assert model1 is model2
        assert model1 is mock_model


class TestStateConcurrency:
    """Test state management under concurrent access"""

    @pytest.mark.asyncio
    async def test_concurrent_session_updates(self):
        """Test concurrent session history updates with lock"""
        set_session_histories({})
        lock = get_session_lock()

        async def update_session(session_id, message):
            async with lock:
                histories = get_session_histories()
                if session_id not in histories:
                    histories[session_id] = []
                histories[session_id].append({"role": "user", "content": message})
                set_session_histories(histories)

        # Run concurrent updates
        await asyncio.gather(
            update_session("session1", "msg1"),
            update_session("session1", "msg2"),
            update_session("session1", "msg3"),
            update_session("session2", "msg4"),
        )

        histories = get_session_histories()
        assert len(histories["session1"]) == 3
        assert len(histories["session2"]) == 1

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self):
        """Test concurrent read and write operations"""
        set_session_histories({})
        lock = get_session_lock()

        async def writer():
            for i in range(10):
                async with lock:
                    histories = get_session_histories()
                    histories[f"session_{i}"] = []
                    set_session_histories(histories)
                await asyncio.sleep(0.001)

        async def reader():
            read_count = 0
            for _ in range(10):
                async with lock:
                    histories = get_session_histories()
                    read_count = len(histories)
                await asyncio.sleep(0.001)
            return read_count

        await asyncio.gather(writer(), reader())

        # Final count should be 10 sessions
        histories = get_session_histories()
        assert len(histories) == 10


class TestStateIsolation:
    """Test that state is properly isolated between operations"""

    def test_session_isolation(self):
        """Test that different sessions are isolated"""
        set_session_histories({})

        histories = get_session_histories()
        histories["session_a"] = [{"role": "user", "content": "A"}]
        histories["session_b"] = [{"role": "user", "content": "B"}]

        assert histories["session_a"][0]["content"] == "A"
        assert histories["session_b"][0]["content"] == "B"

    def test_multiple_sessions_independent(self):
        """Test that multiple sessions can be managed independently"""
        sessions = {
            f"session_{i}": [{"role": "user", "content": f"msg{i}"}] for i in range(5)
        }

        set_session_histories(sessions)
        histories = get_session_histories()

        assert len(histories) == 5
        for i in range(5):
            assert histories[f"session_{i}"][0]["content"] == f"msg{i}"
