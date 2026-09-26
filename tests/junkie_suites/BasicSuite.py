from test_junkie.decorators import test, beforeTest, afterTest, afterClass, beforeClass, Suite


def skip_function(meta):
    assert meta.get("name") == "skip_function"
    return True


@Suite(feature="AdvancedSuite")
class BasicSuite:

    @beforeClass()
    def before_class(self):
        pass

    @beforeTest()
    def before_test(self):
        pass

    @afterTest()
    def after_test(self):
        pass

    @afterClass()
    def after_class(self):
        pass

    @test(tags=["critical2", "v1"])
    def failure(self):
        assert True is False

    @test(tags=["critical2", "v1"])
    def error(self):
        raise Exception("Exception")

    @test(skip=True)
    def skip(self):
        pass

    @test(meta={"name": "skip_function"},
          skip=skip_function)
    def skip_function(self):
        pass

    @test(parameters=[1, 2, 3, 4], tags=["critical2", "v1"])
    def parameters(self, parameter):
        pass

    @test(retry=2)
    def retry(self):
        assert True is False
