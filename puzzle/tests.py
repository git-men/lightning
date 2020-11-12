from django.test import TestCase
from puzzle.models import Block
from puzzle.services import move


class BlockMoveTest(TestCase):
    def setUp(self):
        self.root = Block.objects.create()
        self.child1 = self.root.children.create()
        self.child2 = self.root.children.create()
        self.root2 = Block.objects.create()

    def assertChildren(self, parent, children_id):
        self.assertListEqual(children_id, list(parent.children.values_list('id', flat=True)))

    def test_to_right(self):
        move(self.child1.id, self.root.id, 1)
        self.assertChildren(self.root, [self.child2.id, self.child1.id])

    def test_to_left(self):
        move(self.child2.id, self.root.id, 0)
        self.assertChildren(self.root, [self.child2.id, self.child1.id])

    def test_move(self):
        move(self.child1.id, self.root2.id, 0)
        self.assertChildren(self.root, [self.child2.id])
        self.assertChildren(self.root2, [self.child1.id])
        move(self.child2.id, self.root2.id, 0)
        self.assertChildren(self.root, [])
        self.assertChildren(self.root2, [self.child2.id, self.child1.id])
        move(self.child2.id, self.root.id, 0)
        self.assertChildren(self.root, [self.child2.id])
        self.assertChildren(self.root2, [self.child1.id])
        move(self.child1.id, self.root.id, 1)
        self.assertChildren(self.root, [self.child2.id, self.child1.id])
        self.assertChildren(self.root2, [])
