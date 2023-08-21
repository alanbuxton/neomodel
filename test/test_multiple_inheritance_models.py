from neomodel import (
    IntegerProperty,
    StringProperty,
    StructuredNode,
    db
)
from neomodel.exceptions import NodeClassNotDefined
import pytest

class Square(StructuredNode):
    name = StringProperty()
    side_length = IntegerProperty()

class Circle(StructuredNode):
    name = StringProperty()
    radius = IntegerProperty()

class Red(StructuredNode):
    pass

class Yellow(StructuredNode):
    pass

class RedSquare(Square, Red):
    __class_name_is_label__ = True

class YellowSquare(Square, Yellow):
    __class_name_is_label__ = False  # Will not save a YellowSquare label

class RedCircle(Circle, Red):
    __class_name_is_label__ = None

class YellowCircle(Circle, Yellow):
    pass


def test_multiple_inheritance_creation():
    rs = RedSquare(name="red1", side_length=12)
    ys = YellowSquare(name="yellow1", side_length=13)
    rc = RedCircle(name="red2", radius=14)
    yc = YellowCircle(name="yellow2", radius=15)
    rs.save()
    ys.save()
    rc.save()
    yc.save()
    assert set(rs.labels()) == set( ["RedSquare", "Red", "Square"] )
    assert set(ys.labels()) == set( ["Square", "Yellow"] )
    assert set(rc.labels()) == set( ["Red", "Circle", "RedCircle"] )
    assert set(yc.labels()) == set( ["Yellow", "Circle", "YellowCircle"] )


def test_multiple_inheritance_retrieval():
    cypher_creation = ("""
        CREATE
            (e:Red:Square {name:"FooBar", side_length:22}),
            (f:Yellow:Square {name: "BazQux", side_length:8}),
            (g:Red:Circle {name: "BozBiz", radius: 9  }),
            (h:Yellow:Circle {name: "QazWsx", radius: 42})
    """)
    db.cypher_query(cypher_creation)

    # YellowSquare is only class defined with __class_name_is_label__ == False
    ys_cypher,_ = db.cypher_query('match (n:Square {name:"BazQux"}) return n')
    assert len(ys_cypher) > 0
    ys_neo = Square.nodes.filter(name="BazQux")
    assert len(ys_neo.all()) == len(ys_cypher)

    yc_cypher,_ = db.cypher_query('match (n:Circle {name:"QazWsx"}) return n')
    assert len(yc_cypher) > 0
    yc_neo = Circle.nodes.filter(name="QazWsx")
    with pytest.raises(NodeClassNotDefined):
        assert len(yc_neo.all()) == len(yc_cypher)


def test_cannot_directly_filter_where_class_name_is_not_label():
    rs = RedSquare(name="red3", side_length=22)
    ys = YellowSquare(name="yellow3", side_length=23)
    rs.save()
    ys.save()

    red_nodes = RedSquare.nodes.filter(name="red3")
    assert len(red_nodes) == 1
    yellow_nodes = YellowSquare.nodes.filter(name="yellow3")
    assert len(yellow_nodes) == 0
