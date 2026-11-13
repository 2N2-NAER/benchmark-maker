import argparse
import json
import sys
from .pipeline import extract_document, load_assets, read_json, retrieve, validate_plan, export_run, run, write_json

def main(argv=None):
    p = argparse.ArgumentParser(description='AI-driven benchmark synthesis. No frontend required.')
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('extract', help='Read a problem document for the AI host'); a.add_argument('document'); a.add_argument('--out')
    a = sub.add_parser('search', help='Search captioned local catalog using an AI-authored plan'); a.add_argument('--plan', required=True); a.add_argument('--assets', required=True); a.add_argument('--out', required=True); a.add_argument('--limit', type=int, default=20)
    a = sub.add_parser('finalize', help='Validate AI-authored cases, resolve media IDs, export candidates'); a.add_argument('--plan', required=True); a.add_argument('--assets', required=True); a.add_argument('--cases', required=True); a.add_argument('--out', required=True)
    a = sub.add_parser('run', help='Run all AI stages with a configured model endpoint'); a.add_argument('document'); a.add_argument('--assets', required=True); a.add_argument('--out', required=True); a.add_argument('--count', type=int, default=60); a.add_argument('--domain', choices=['漫剧','电商','双业务'], default='双业务'); a.add_argument('--resume', action='store_true'); a.add_argument('--examples', help='Real user input examples as a local UTF-8 document')
    sub.add_parser('mcp', help='Start MCP stdio server for an AI host')
    args = p.parse_args(argv)
    try:
        if args.command == 'mcp':
            from .mcp import serve
            serve(); return
        if args.command == 'extract':
            result = extract_document(args.document)
            if args.out: write_json(args.out, result)
        elif args.command == 'search':
            result = retrieve(read_json(args.plan), load_assets(args.assets), args.limit); write_json(args.out, result)
        elif args.command == 'finalize':
            value = read_json(args.cases)
            result = export_run(args.out, value.get('cases') if isinstance(value,dict) else value, read_json(args.plan), load_assets(args.assets))
        else:
            result = run(args.document, args.assets, args.out, count=args.count, domains=['漫剧','电商'] if args.domain=='双业务' else [args.domain], resume=args.resume, examples=extract_document(args.examples)['text'] if args.examples else '')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == 'finalize' and (result['blocked'] or result['global_errors']): return 2
    except Exception as exc:
        # Never print endpoint headers, API keys or raw provider responses.
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr); return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
