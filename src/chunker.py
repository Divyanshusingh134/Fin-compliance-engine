class Chunker:
    def __init__(self, blocks, max_words = 350):
        self.chunks = []
        self.cur = []
        self.n = 0
        self.path = {}
        self.blocks = blocks
        self.max_words = max_words

    def heading_path(self) ->str:
        return " > ".join(self.path[k] for k in sorted(self.path))


    def flush(self):
        if self.cur:
            self.chunks.append({"type": "text", "heading_path": self.heading_path(), "text": self.heading_path() + "\n" + "\n\n".join(self.cur)})
        self.cur = []
        self.n = 0


    def walk(self):

        for b in self.blocks:
            if b.kind == "heading":
                if b.level <= 3:
                    self.flush()

                self.path[b.level] = b.text
                for k in [k for k in self.path if k > b.level]: del self.path[k]
            elif b.kind == "table":
                self.flush()
                self.chunks.append({"type": "table", "heading_path": self.heading_path(), "text": self.heading_path() + "\n" + b.text, "rows": b.rows})
                
            else:
                w = len(b.text.split())
                if self.n + w > self.max_words:
                    self.flush()

                self.cur.append(b.text)
                self.n += w
        
        self.flush()
        return self.chunks

        
