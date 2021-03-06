__author__ = 'wuyihao'
from operator import itemgetter
import math

class UserCF:
    def __init__(self):
        self.user_item = {}
        self.item_user = {}
        self.user_user = {}
        self.rank = {}
        self.N = {}

    def read_from_file(self, filename):
        with open(filename) as f:
            for line in f.readlines():
                line = map(int, line.split())
                if line[1] not in self.item_user:
                    self.item_user[line[1]] = set()
                self.item_user[line[1]].add(line[0])

                if line[0] not in self.user_item:
                    self.user_item[line[0]] = set()
                self.user_item[line[0]].add(line[1])

    def train(self):
        # Because user_user matrix is sparse, this algorithm does speed up usercf
        # The plain algorithm O(U*C) where C is total number of users' collections
        #       O(U^2 * c) = O(U^2 * C/U) = O(U*C), and it's not accurate, because
        #       the complexity of intersection of two sets is slightly greater than O(c)
        # The new algorithm O(C^2/I)
        #       O(I * i^2) where i is average number of collectors of an item
        #      =O(I * C*C/I/I) = O(C*C/I)
        # When I*U > C, which means sparse, the new algorithm is faster!!!

        # Rehash from origin data set
        for item, v in self.item_user.iteritems():
            for user in v:
                if user not in self.user_user:
                    self.user_user[user] = dict()
                for user2 in v:
                    if user2 != user:
                        if user2 not in self.user_user[user]:
                            # The W matrix
                            self.user_user[user][user2] = 0
                        self.user_user[user][user2] += 1
        for u, vw in self.user_user.iteritems():
            for v, w in vw.iteritems():
                self.user_user[u][v] /= math.sqrt(len(self.user_item[u])*len(self.user_item[v]))

    def recommend(self, target, k):
        interacted_items = self.user_item[target]
        # Only refer to top k related user, k is not the bigger the better
        for v, w in sorted(self.user_user[target].items(), key=itemgetter(1), reverse=True)[0:k]:
            for item in self.user_item[v]:
                # Don't recommend what's already known to me
                if item not in interacted_items:
                    if item not in self.rank:
                        self.rank[item] = 0
                    self.rank[item] += w
        self.rank = sorted(self.rank)
        return self.rank

if __name__ == '__main__':
    usercf = UserCF()
    usercf.read_from_file('/tmp/try')
    usercf.train()
    usercf.recommend(3, 2)
