from test_junkie.decorators import test, beforeTest, afterTest, afterClass, beforeClass, Suite


def skip_function(meta):
    assert meta.get("name") == "skip_function"
    return True


@Suite()
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

    @test()
    def failure(self):
        assert True is False

    @test()
    def error(self):
        raise Exception("Exception")

    @test(skip=True)
    def skip(self):
        pass

    @test(meta={"name": "skip_function"},
          skip=skip_function)
    def skip_function(self):
        pass

    @test(parameters=[1, 2, 3, 4])
    def parameters(self, parameter):
        pass

    @test(retry=2)
    def retry(self):
        assert True is False
