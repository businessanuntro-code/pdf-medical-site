const fs = require("fs-extra");
const AdmZip = require("adm-zip");
const xml2js = require("xml2js");

const INPUT = "template.idml";
const OUTPUT = "output/output.idml";

const data = {
  title: "Articol Medical: Diabet Tip 2",
  body: "Acesta este conținutul generat automat pentru secțiunea medicală."
};

async function run() {
  const zip = new AdmZip(INPUT);
  const tempDir = "./temp";

  zip.extractAllTo(tempDir, true);

  const storiesDir = `${tempDir}/Stories`;
  const files = fs.readdirSync(storiesDir);

  const parser = new xml2js.Parser();
  const builder = new xml2js.Builder();

  for (const file of files) {
    const path = `${storiesDir}/${file}`;
    const xml = fs.readFileSync(path, "utf8");

    const parsed = await parser.parseStringPromise(xml);

    const content =
      parsed.Story?.ParagraphStyleRange?.[0]?.CharacterStyleRange?.[0]?.Content?.[0];

    if (!content) continue;

    const lower = content.toLowerCase();

    if (lower.includes("title")) {
      parsed.Story.ParagraphStyleRange[0].CharacterStyleRange[0].Content[0] =
        data.title;
    }

    if (lower.includes("body")) {
      parsed.Story.ParagraphStyleRange[0].CharacterStyleRange[0].Content[0] =
        data.body;
    }

    const updated = builder.buildObject(parsed);
    fs.writeFileSync(path, updated);
  }

  const newZip = new AdmZip();
  newZip.addLocalFolder(tempDir);
  newZip.writeZip(OUTPUT);

  console.log("DONE →", OUTPUT);
}

run();
