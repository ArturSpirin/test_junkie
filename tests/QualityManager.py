import logging




class QualityManager:

    @staticmethod
    def check_class_metrics(metrics,
                            expected_retry_count=1,
                            expected_status="success",
                            expected_runtime=0,

                            expected_afterclass_exception_count=0,
                            expected_beforeclass_exception_count=0,
                            expected_aftertest_exception_count=0,
                            expected_beforetest_exception_count=0,

                            expected_afterclass_exception_object=None,
                            expected_beforeclass_exception_object=None,
                            expected_aftertest_exception_object=None,
                            expected_beforetest_exception_object=None,

                            expected_afterclass_performance_count=0,
                            expected_beforeclass_performance_count=0,
                            expected_aftertest_performance_count=0,
                            expected_beforetest_performance_count=0,

                            expected_afterclass_performance_time=0,
                            expected_beforeclass_performance_time=0,
                            expected_aftertest_performance_time=0,
                            expected_beforetest_performance_time=0):

        assert metrics["retry"] == expected_retry_count, \
            "Expected retry count: {} Actual retry count: {}".format(expected_retry_count, metrics["retry"])
        assert metrics["status"] == expected_status
        assert metrics["runtime"] >= expected_runtime

        assert len(metrics["afterClass"]["exceptions"]) == expected_afterclass_exception_count
        for i in metrics["afterClass"]["exceptions"]:
            assert type(i) == type(expected_afterclass_exception_object) \
                if not isinstance(expected_afterclass_exception_object, type) else expected_afterclass_exception_object

        assert len(metrics["afterClass"]["performance"]) == expected_afterclass_performance_count
        for i in metrics["afterClass"]["performance"]:
            assert i >= expected_afterclass_performance_time

        assert len(metrics["beforeClass"]["exceptions"]) == expected_beforeclass_exception_count
        for i in metrics["beforeClass"]["exceptions"]:
            assert type(i) == type(expected_beforeclass_exception_object) \
                if not isinstance(expected_beforeclass_exception_object, type) else expected_beforeclass_exception_object

        assert len(metrics["beforeClass"]["performance"]) == expected_beforeclass_performance_count
        for i in metrics["beforeClass"]["performance"]:
            assert i >= expected_beforeclass_performance_time

        assert len(metrics["afterTest"]["exceptions"]) == expected_aftertest_exception_count, \
            "Expected: {} Actual: {}".format(expected_aftertest_exception_count,
                                             len(metrics["afterTest"]["exceptions"]))
        for i in metrics["afterTest"]["exceptions"]:
            assert type(i) == type(expected_aftertest_exception_object) \
                if not isinstance(expected_aftertest_exception_object, type) else expected_aftertest_exception_object

        assert len(metrics["afterTest"]["performance"]) == expected_aftertest_performance_count, \
            "Expected: {} Actual: {}".format(expected_aftertest_performance_count,
                                             len(metrics["afterTest"]["performance"]))
        for i in metrics["afterTest"]["performance"]:
            assert i >= expected_aftertest_performance_time

        assert len(metrics["beforeTest"]["exceptions"]) == expected_beforetest_exception_count, \
            "Expected: {} Actual: {}".format(expected_beforetest_exception_count,
                                             len(metrics["beforeTest"]["exceptions"]))
        for i in metrics["beforeTest"]["exceptions"]:
            assert type(i) == type(expected_beforetest_exception_object) \
                if not isinstance(expected_beforetest_exception_object, type) else expected_beforetest_exception_object

        assert len(metrics["beforeTest"]["performance"]) == expected_beforetest_performance_count, \
            "Expected: {} Actual: {}".format(expected_beforetest_performance_count,
                                             len(metrics["beforeTest"]["performance"]))
        for i in metrics["beforeTest"]["performance"]:
            assert i >= expected_beforetest_performance_time

    @staticmethod
    def check_test_metrics(metrics,
                           expected_retry_count=1,
                           expected_status="success",
                           expected_param=None,
                           expected_class_param=None,
                           expected_exception_count=1,
                           expected_exception=None,
                           expected_performance_count=1,
                           expected_performance=0):

        assert metrics["status"] == expected_status, \
            "Expected status: {} Actual Status: {}".format(expected_status, metrics["status"])
        assert metrics["retry"] == expected_retry_count, \
            "Expected retry: {} Actual: {}".format(expected_retry_count, metrics["retry"])
        assert str(metrics["param"]) == str(expected_param)
        assert str(metrics["class_param"]) == str(expected_class_param)

        assert len(metrics["exceptions"]) == expected_exception_count
        for i in metrics["exceptions"]:
            assert type(i) == type(expected_exception) \
                if not isinstance(expected_exception, type) else expected_exception

        assert len(metrics["performance"]) == expected_performance_count
        for i in metrics["performance"]:
            assert i >= expected_performance

    @staticmethod
    def setting_sources(runner_kwargs):
        """
        Builds Settings from runner_kwargs and returns {setting: source} as reported in the debug log,
        e.g. {"html_report": "KWARGS", "test_multithreading_limit": "DEFAULTS"}
        """
        from test_junkie.debugger import LogJunkie
        from test_junkie.settings import Settings

        messages = []
        handler = logging.Handler()
        handler.emit = lambda record: messages.append(record.getMessage())
        logger = logging.getLogger("TestJunkieLogger")
        previous_level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        LogJunkie.enable_logging(10)
        try:
            Settings(runner_kwargs=dict(runner_kwargs), run_kwargs={})
        finally:
            LogJunkie.disable_logging()
            logger.removeHandler(handler)
            logger.setLevel(previous_level)
        sources = {}
        for message in messages:
            if message.startswith("Setting: "):
                setting, source = message[len("Setting: "):].split(" Source: ")
                sources[setting] = source
        return sources
