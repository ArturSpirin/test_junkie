from test_junkie.decorators import Suite, test


@Suite(owner="John Doe")
class SkipOwner:

    @test()
    def test_1(self):
        pass

    @test(owner="Jane Doe")
    def test_2(self):
        pass

    @test()
    def test_3(self):
        pass


@Suite(feature="Login")
class SkipFeature:

    @test()
    def test_1(self):
        pass

    @test()
    def test_2(self):
        pass

    @test()
    def test_3(self):
        pass


@Suite(feature="Login")
class SkipComponent:

    @test()
    def test_1(self):
        pass

    @test(component="Auth API")
    def test_2(self):
        pass

    @test()
    def test_3(self):
        pass


@Suite()
class SkipTests:

    @test()
    def test_1(self):
        pass

    @test()
    def test_2(self):
        pass

    @test()
    def test_3(self):
        pass
