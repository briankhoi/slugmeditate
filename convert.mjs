import {
    createReadStream,
    readFileSync,
    writeFileSync,
    unlinkSync
} from 'fs';
import { Readable } from 'stream';
import path from 'path';

import {
    loadPly,
    loadSpz,
    serializePly,
    serializeSpz
} from 'spz-js';

// Helper function to load either SPZ or PLY files
const loadFile = async (file) => {
    const extension = path.extname(file);
    if (extension === '.spz') {
        const fileBuffer = readFileSync(file);
        return await loadSpz(fileBuffer);
    } else if (extension === '.ply') {
        const fileStream = createReadStream(file);
        const webStream = Readable.toWeb(fileStream);
        return await loadPly(webStream);
    }
    throw new Error(`Unsupported file extension: ${extension}`);
};

const gs = await loadFile("luma_splat.ply"); // or gs.spz

// const plyData = serializePly(gs);
// writeFileSync("gs.ply", Buffer.from(plyData));

const spzData = await serializeSpz(gs);
writeFileSync("luma_splat.spz", Buffer.from(spzData));