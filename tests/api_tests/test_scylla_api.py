import pytest

from scylla_api_client.api import ScyllaApi


@pytest.fixture(scope="module")
def scylla_api_obj(api_server):
    scylla_api = ScyllaApi(api_server.host, api_server.port)
    scylla_api.load()
    return scylla_api


def test_number_of_scylla_api_modules(scylla_api_obj):
    assert len(scylla_api_obj.modules) == 4


def test_module_names(scylla_api_obj):
    module_names = ["system", "compaction_manager", "error_injection", "v2"]

    for module, expected_name in zip(scylla_api_obj.modules, module_names):
        assert module == expected_name


def test_module_commands(scylla_api_obj):
    module = "system"
    module_commands = ["logger", "drop_sstable_caches", "uptime_ms", "logger/{name}"]
    current_module = scylla_api_obj.modules["system"]
    assert current_module.name == module
    assert list(current_module.commands.keys()) == module_commands


def test_command_parameters(scylla_api_obj):
    module = "compaction_manager"
    module_command = [
        'compactions', 'compaction_history',
        'compaction_info', 'force_user_defined_compaction',
        'stop_compaction', 'metrics/pending_tasks',
        'metrics/pending_tasks_by_table',
        'metrics/completed_tasks',
        'metrics/total_compactions_completed']
    command = "compactions"
    current_module = scylla_api_obj.modules["compaction_manager"]
    current_command = current_module.commands["compactions"]
    assert current_command.name == command

