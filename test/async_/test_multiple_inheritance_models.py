from test._async_compat import mark_async_test

import pytest

from neomodel import AsyncStructuredNode, IntegerProperty, StringProperty, adb
from neomodel.exceptions import NodeClassNotDefined


class Square(AsyncStructuredNode):
    name = StringProperty()
    side_length = IntegerProperty()


class Circle(AsyncStructuredNode):
    name = StringProperty()
    radius = IntegerProperty()


class Red(AsyncStructuredNode):
    pass


class Yellow(AsyncStructuredNode):
    pass


class RedSquare(Square, Red):
    __class_name_is_label__ = True


class YellowSquare(Square, Yellow):
    __class_name_is_label__ = False  # Will not save a YellowSquare label


class RedCircle(Circle, Red):
    __class_name_is_label__ = None


class YellowCircle(Circle, Yellow):
    pass


@mark_async_test
async def test_multiple_inheritance_creation():
    rs = await RedSquare(name="red1", side_length=12).save()
    ys = await YellowSquare(name="yellow1", side_length=13).save()
    rc = await RedCircle(name="red2", radius=14).save()
    yc = await YellowCircle(name="yellow2", radius=15).save()
    assert set(await rs.labels()) == set(["RedSquare", "Red", "Square"])
    assert set(await ys.labels()) == set(["Square", "Yellow"])
    assert set(await rc.labels()) == set(["Red", "Circle", "RedCircle"])
    assert set(await yc.labels()) == set(["Yellow", "Circle", "YellowCircle"])


@mark_async_test
async def test_multiple_inheritance_retrieval():
    cypher_creation = """
        CREATE
            (e:Red:Square {name:"FooBar", side_length:22}),
            (f:Yellow:Square {name: "BazQux", side_length:8}),
            (g:Red:Circle {name: "BozBiz", radius: 9  }),
            (h:Yellow:Circle {name: "QazWsx", radius: 42})
    """
    await adb.cypher_query(cypher_creation)

    # YellowSquare is only class defined with __class_name_is_label__ == False
    ys_cypher, _ = await adb.cypher_query('match (n:Square {name:"BazQux"}) return n')
    assert len(ys_cypher) > 0
    ys_neo = await Square.nodes.filter(name="BazQux").all()
    assert len(ys_neo) == len(ys_cypher)

    yc_cypher, _ = await adb.cypher_query('match (n:Circle {name:"QazWsx"}) return n')
    assert len(yc_cypher) > 0
    with pytest.raises(NodeClassNotDefined):
        await Circle.nodes.filter(name="QazWsx").all()


@mark_async_test
async def test_cannot_directly_filter_where_class_name_is_not_label():
    rs = await RedSquare(name="red3", side_length=22).save()
    ys = await YellowSquare(name="yellow3", side_length=23).save()

    red_nodes = await RedSquare.nodes.filter(name="red3").all()
    assert len(red_nodes) == 1
    yellow_nodes = await YellowSquare.nodes.filter(name="yellow3").all()
    assert len(yellow_nodes) == 0
