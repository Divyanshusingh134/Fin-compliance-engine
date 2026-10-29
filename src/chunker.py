class Chunker:
    def __init__(self, blocks, max_words = 350):
        self.chunks = []
        self.cur = []
        self.n = 0
        self.path = {}
        self.blocks = blocks
        self.max_words = max_words

    def hp(self):
        pass


    def flush(self):
        pass

    def walk(self):

        for b in self.blocks:
            if b.kind == "heading":
                if b.level <= 3:
                    self.flush()

                self.path[b.level] = b.text
                for k in [k for k in self.path if k > b.level]: del self.path[k]
            elif b.kind == "table":
                pass
            else:
                w = len(b.text.split())
                if self.n + w > self.max_words:
                    self.flush()

                self.cur.append(b.text)
                self.n += w

