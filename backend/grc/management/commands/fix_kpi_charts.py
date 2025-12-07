"""
Django management command to fix KPI display types
Usage: python manage.py fix_kpi_charts [--preview] [--kpi-id ID --type TYPE]
"""

from django.core.management.base import BaseCommand
from grc.routes.Global.update_kpi_display_types import (
    preview_kpi_changes,
    analyze_and_update_kpis,
    fix_specific_kpi,
    show_available_chart_types
)


class Command(BaseCommand):
    help = 'Analyze and fix KPI display types to ensure proper chart visualization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Preview changes without applying them',
        )
        parser.add_argument(
            '--kpi-id',
            type=int,
            help='Update a specific KPI by ID',
        )
        parser.add_argument(
            '--type',
            type=str,
            help='Display type to set for specific KPI (use with --kpi-id)',
        )
        parser.add_argument(
            '--show-types',
            action='store_true',
            help='Show available chart types',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔧 KPI Chart Type Fixer\n'))
        
        # Show available chart types
        if options['show_types']:
            show_available_chart_types()
            return
        
        # Fix specific KPI
        if options['kpi_id']:
            if not options['type']:
                self.stdout.write(
                    self.style.ERROR('❌ Error: --type is required when using --kpi-id')
                )
                self.stdout.write('\nRun with --show-types to see available chart types')
                return
            
            success = fix_specific_kpi(options['kpi_id'], options['type'])
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ Successfully updated KPI #{options["kpi_id"]}\n')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'\n❌ Failed to update KPI #{options["kpi_id"]}\n')
                )
            return
        
        # Preview or apply changes to all KPIs
        if options['preview']:
            self.stdout.write(self.style.WARNING('Preview mode - no changes will be made\n'))
            preview_kpi_changes()
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  This will update KPI display types in the database\n')
            )
            
            # Confirm before proceeding
            confirm = input('Do you want to proceed? (yes/no): ')
            if confirm.lower() in ['yes', 'y']:
                updated = analyze_and_update_kpis(dry_run=False)
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ Successfully updated {updated} KPIs!\n')
                )
                self.stdout.write(
                    self.style.SUCCESS('🎨 Refresh your frontend to see the charts!\n')
                )
            else:
                self.stdout.write(self.style.WARNING('\n❌ Operation cancelled\n'))

