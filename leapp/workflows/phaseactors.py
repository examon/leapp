from leapp.exceptions import CyclingDependenciesError


class PhaseActors(object):
    def __init__(self, actors, stage):
        self.stage = stage
        self._actors = actors
        self._consumes = set()
        self._produces = set()
        self._messages = {}

        for actor in self._actors:
            self._consumes.update(actor.consumes)
            self._produces.update(actor.produces)
            for message in actor.produces:
                self._messages.setdefault(message.__name__,
                                          {'type': message, 'producers': []})['producers'].append(actor)
            for message in actor.consumes:
                self._messages.setdefault(message.__name__, {'type': message, 'producers': []})
        self._initial = self._consumes - self._produces
        self._sort()

    @property
    def initial(self):
        return tuple(self._initial)

    @property
    def actors(self):
        return tuple(self._actors)

    @property
    def consumes(self):
        return tuple(self._consumes)

    @property
    def produces(self):
        return tuple(self._produces)

    def _sort(self):
        actors, self._actors = list(self._actors), ()
        while actors:
            scheduled = []
            for idx, actor in enumerate(actors):
                for message in actor.consumes:
                    if self._messages[message.__name__]['producers']:
                        break
                else:
                    for message in actor.produces:
                        self._messages[message.__name__]['producers'].remove(actor)

                    scheduled.append(idx)
                    self._actors += (actor,)

            if not scheduled:
                raise CyclingDependenciesError(
                    "Could not solve dependency order for '{}'".format(', '.join([actor.name for actor in actors])))

            for idx in reversed(scheduled):
                actors.pop(idx)
