"""Tests for ParkPartner dependency injection"""

from collections.abc import Callable

from app.adapters.llm.ollama import call_ollama
from app.adapters.stt.whisper import transcribe_audio
from app.adapters.tts.edge import synthesize_speech
from app.core.dependencies import Dependencies, deps


class TestDependenciesDataclass:
    """Test Dependencies dataclass"""

    def test_dependencies_creation(self):
        """Test Dependencies can be created"""
        dependencies = Dependencies()
        assert dependencies is not None

    def test_dependencies_has_stt_fn(self):
        """Test Dependencies has stt_fn attribute"""
        dependencies = Dependencies()
        assert hasattr(dependencies, "stt_fn")
        assert isinstance(dependencies.stt_fn, Callable)

    def test_dependencies_has_llm_fn(self):
        """Test Dependencies has llm_fn attribute"""
        dependencies = Dependencies()
        assert hasattr(dependencies, "llm_fn")
        assert isinstance(dependencies.llm_fn, Callable)

    def test_dependencies_has_tts_fn(self):
        """Test Dependencies has tts_fn attribute"""
        dependencies = Dependencies()
        assert hasattr(dependencies, "tts_fn")
        assert isinstance(dependencies.tts_fn, Callable)

    def test_dependencies_default_functions(self):
        """Test Dependencies uses correct default functions"""
        dependencies = Dependencies()

        assert dependencies.stt_fn == transcribe_audio
        assert dependencies.llm_fn == call_ollama
        assert dependencies.tts_fn == synthesize_speech

    def test_dependencies_custom_functions(self):
        """Test Dependencies can be created with custom functions"""
        custom_stt = lambda *args: "custom stt"  # noqa: E731
        custom_llm = lambda *args: "custom llm"  # noqa: E731
        custom_tts = lambda *args: "custom tts"  # noqa: E731

        dependencies = Dependencies(
            stt_fn=custom_stt,
            llm_fn=custom_llm,
            tts_fn=custom_tts,
        )

        assert dependencies.stt_fn == custom_stt
        assert dependencies.llm_fn == custom_llm
        assert dependencies.tts_fn == custom_tts


class TestGlobalDepsInstance:
    """Test global deps instance"""

    def test_deps_exists(self):
        """Test global deps instance exists"""
        assert deps is not None

    def test_deps_is_dependencies(self):
        """Test global deps is Dependencies instance"""
        assert isinstance(deps, Dependencies)

    def test_deps_stt_fn(self):
        """Test global deps stt_fn"""
        assert deps.stt_fn == transcribe_audio

    def test_deps_llm_fn(self):
        """Test global deps llm_fn"""
        assert deps.llm_fn == call_ollama

    def test_deps_tts_fn(self):
        """Test global deps tts_fn"""
        assert deps.tts_fn == synthesize_speech

    def test_deps_singleton(self):
        """Test that deps is a singleton instance"""
        from app.core.dependencies import deps as deps2

        assert deps is deps2


class TestDependencyFunctions:
    """Test that dependency functions have correct signatures"""

    def test_stt_fn_is_callable(self):
        """Test stt_fn is callable"""
        assert callable(deps.stt_fn)

    def test_llm_fn_is_callable(self):
        """Test llm_fn is callable"""
        assert callable(deps.llm_fn)

    def test_tts_fn_is_callable(self):
        """Test tts_fn is callable"""
        assert callable(deps.tts_fn)

    def test_stt_fn_is_async(self):
        """Test stt_fn is async function"""
        import asyncio

        assert asyncio.iscoroutinefunction(deps.stt_fn)

    def test_tts_fn_is_async(self):
        """Test tts_fn is async function"""
        import asyncio

        assert asyncio.iscoroutinefunction(deps.tts_fn)

    def test_llm_fn_is_sync(self):
        """Test llm_fn is sync function"""
        import asyncio

        assert not asyncio.iscoroutinefunction(deps.llm_fn)


class TestDependencyInjection:
    """Test dependency injection patterns"""

    def test_dependencies_can_be_passed(self):
        """Test Dependencies can be passed as argument"""

        def use_deps(d: Dependencies):
            return d.stt_fn

        result = use_deps(deps)
        assert result == transcribe_audio

    def test_dependencies_attribute_access(self):
        """Test Dependencies attributes can be accessed"""
        d = deps

        stt = d.stt_fn
        llm = d.llm_fn
        tts = d.tts_fn

        assert stt == transcribe_audio
        assert llm == call_ollama
        assert tts == synthesize_speech

    def test_dependencies_unpacking(self):
        """Test Dependencies can be unpacked"""
        d = deps

        stt_fn = d.stt_fn
        llm_fn = d.llm_fn
        tts_fn = d.tts_fn

        assert callable(stt_fn)
        assert callable(llm_fn)
        assert callable(tts_fn)
