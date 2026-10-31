import { readFile, writeFile } from 'node:fs/promises';
const source = new URL('../../database/schema.prisma', import.meta.url);
const target = new URL('../prisma/schema.prisma', import.meta.url);
const schema = (await readFile(source, 'utf8')).replace('../backend/generated/client', '../generated/client');
await writeFile(target, schema);
console.log('Synced database/schema.prisma → backend/prisma/schema.prisma');
