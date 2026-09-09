const express = require("express");
const cors = require("cors");

const app = express();

app.use(cors());
app.use(express.json());

app.use("/snapshots", express.static("../snapshots"));

app.get("/", (req, res) => {
    res.json({
        message: "Trinetra backend is running"
    });
});

app.get("/api/events", (req, res) => {
    const fs = require("fs");

    fs.readFile("../events.json", "utf8", (err, data) => {
        if (err) {
            return res.status(500).json({
                error: "Could not read events"
            });
        }

        res.json(JSON.parse(data));
    });
});

const PORT = 5000;

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});