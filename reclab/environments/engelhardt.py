import numpy as np
import scipy
import scipy.special

from . import environment

"""
Implementation of "How How Algorithmic Confounding in Recommendation Systems Increases Homogeneity and Decreases Utility" by Chaney, Stewart, and Engelhardt (2018).
"""

class User(object):
    def __init__(self, num_topics, known_util_weight, user_topic_weights, beta_var):
        self.num_topics = num_topics
        alpha = ((1 - known_util_weight) / (beta_var ** 2) - (1 / known_util_weight)) * (known_util_weight ** 2)
        beta = alpha * ((1 / known_util_weight) - 1)
        self.known_util_weight = np.random.beta(alpha, beta)
        self.preferences = np.random.dirichlet(user_topic_weights)

    # returns true utility and known utility
    def rate(self, item_attributes):
        true_util = np.dot(self.preferences, item_attributes) * 5
        return true_util, true_util * self.known_util_weight

class Engelhardt(environment.DictEnvironment):
    def __init__(self, num_topics, num_users, num_items,
                 rating_frequency=0.2, num_init_ratings=0, known_util_weight=0.98, beta_var = 10 ** -5):

        self.known_util_weight = known_util_weight
        self.beta_var = beta_var
        self.user_topic_weights = scipy.special.softmax(np.random.rand(num_topics))
        self.item_topic_weights = scipy.special.softmax(np.random.rand(num_topics))
        self._num_topics = num_topics
        self._num_users = num_users
        self._num_items = num_items
        self._rating_frequency=rating_frequency
        self._num_init_ratings = num_init_ratings
        self._users = None
        self._users_full = None
        self._items = None
        self._ratings = None
        self._timestep = 0

    def _reset_state(self):
        """Reset the environment to its original state. Must be called before the first step.

        Returns
        -------
        users : np.ndarray
            This will always be an array where every row has
            size 0 since users don't have features.
        items : np.ndarray
            This will always be an array where every row has
            size 0 since items don't have features.
        ratings : np.ndarray
            The initial ratings where ratings[i, 0] corresponds to the id of the user that
            made the rating, ratings[i, 1] corresponds to the id of the item that was rated
            and ratings[i, 2] is the rating given to that item.
        util : np.ndarray
            The initial ratings where util[i, 0] corresponds to the id of the user that
            made the rating, util[i, 1] corresponds to the id of the item that was rated
            and util[i, 2] is the true utility given of the interaction.
        """
        self._users_full = {user_id: User(self._num_topics, self.known_util_weight, self.user_topic_weights, self.beta_var)
                         for user_id in range(self._num_users)}
        self._users = {user_id: self._users_full[user_id].preferences for user_id in range(self._num_users)}
        self._items = {item_id: np.random.dirichlet(self.item_topic_weights) for item_id in range(self._num_items)}
        # self._util = scipy.sparse.dok_matrix((self._num_users, self._num_items))

    def _rate_item(self, user_id, item_id):
        """Get a user to rate an item and update the internal rating state.

        Parameters
        ----------
        user_id : int
            The id of the user making the rating.
        item_id : int
            The id of the item being rated.

        Returns
        -------
        rating : int
            The rating the item was given by the user.
        """
        item_attr = self._items[item_id]
        util, rating = self._users_full[user_id].rate(item_attr)
        print("Util is {} and rating is {}".format(util, rating))
        return rating
