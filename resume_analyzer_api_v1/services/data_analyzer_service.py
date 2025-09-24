import logging
from datetime import datetime, timedelta # <--- ADD timedelta here
from collections import defaultdict
from utils.date_utils import DateUtil # Import DateUtil
from matchai.models.resume_models import ResumeProfile, Experience, Skills, Project, SkillEntry, SkillPeriod, NestedPeriod 
from typing import Dict, List, Any, Optional,Tuple
import re # Make sure re is imported


logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root logger or set explicitly

class DataAnalyzerService:
    """
    Performs various calculations on parsed resume data.
    """
    def __init__(self):
        logger.info("DataAnalyzerService initialized.")

    def get_recent_skills_with_experience(self, parsed_data: Dict[str, Any], recent_years: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves skills that have *any* usage period within a specified recent number of years,
        along with their *recent* aggregated experience_years and *recent* periods.
        This provides a view of currently relevant skills.

        Args:
            parsed_data (Dict[str, Any]): The complete parsed profile data.
            recent_years (int): The number of years back from the current date to consider as 'recent'.

        Returns:
            Dict[str, List[Dict[str, Any]]]: A dictionary where keys are skill categories
                                             and values are lists of skill objects (name, recent_experience_years, recent_periods)
                                             that were active within the recent window.
        """
        # Define the recent time window
        current_date_no_tz = datetime.now().replace(tzinfo=None)
        recent_threshold_date = current_date_no_tz - timedelta(days=recent_years * 365.25)
        
        # This will store skill_name -> list of (start_date, end_date) intervals
        # only for periods falling within the recent window.
        recent_skill_intervals_agg = defaultdict(list) 

        # 1. Gather all skill names from the 'skills' section (to know what skills to track)
        all_skill_names_from_skills_section = set()
        skills_data = parsed_data.get('skills')
        if isinstance(skills_data, dict):
            for category_skills_list in skills_data.values():
                if isinstance(category_skills_list, list):
                    for skill_item_dict_or_str in category_skills_list:
                        if isinstance(skill_item_dict_or_str, dict) and skill_item_dict_or_str.get('name'):
                            all_skill_names_from_skills_section.add(skill_item_dict_or_str['name'].strip().lower())
                        elif isinstance(skill_item_dict_or_str, str):
                            all_skill_names_from_skills_section.add(skill_item_dict_or_str.strip().lower())
        elif isinstance(skills_data, list):
            for skill_item_dict_or_str in skills_data:
                if isinstance(skill_item_dict_or_str, dict) and skill_item_dict_or_str.get('name'):
                    all_skill_names_from_skills_section.add(skill_item_dict_or_str['name'].strip().lower())
                elif isinstance(skill_item_dict_or_str, str):
                    all_skill_names_from_skills_section.add(skill_item_dict_or_str.strip().lower())

        # 2. Iterate through ALL experience entries and identify relevant skills AND their intervals
        #    Only collect intervals that overlap with the recent window.
        experience_entries = parsed_data.get('experience', [])
        if experience_entries:
            for exp in experience_entries:
                exp_from_str = exp.get('from')
                exp_to_str = exp.get('to')
                exp_technologies = exp.get('technologies', [])
                exp_description = exp.get('description', '').lower()

                if not exp_from_str or not exp_to_str:
                    continue

                try:
                    exp_from_date = DateUtil.parse_date_flexible(exp_from_str)
                    exp_to_date = DateUtil.parse_date_flexible(exp_to_str)
                    
                    # Determine actual overlap period with the recent window
                    # recent_window_start is recent_threshold_date
                    # recent_window_end is current_date_no_tz (today)
                    
                    # Calculate the intersection of the experience interval and the recent window
                    overlap_start = max(exp_from_date, recent_threshold_date)
                    overlap_end = min(exp_to_date, current_date_no_tz)

                    # If there's no valid overlap (start is after end), skip
                    if overlap_start > overlap_end:
                        continue 
                    
                    # This is the actual interval within the recent window
                    recent_overlap_interval = (overlap_start, overlap_end)

                    # Check technologies explicitly mentioned in this experience entry
                    for tech in exp_technologies:
                        normalized_tech = tech.strip().lower()
                        if normalized_tech in all_skill_names_from_skills_section:
                            recent_skill_intervals_agg[normalized_tech].append(recent_overlap_interval)
                    
                    # Search for skills from general skills list within this experience's description
                    for skill_name_normalized in all_skill_names_from_skills_section:
                        if re.search(r'\b' + re.escape(skill_name_normalized) + r'\b', exp_description, re.IGNORECASE):
                            recent_skill_intervals_agg[skill_name_normalized].append(recent_overlap_interval)
                        elif skill_name_normalized.replace(' ', '-').lower() in exp_description or \
                             skill_name_normalized.replace('-', ' ').lower() in exp_description:
                            recent_skill_intervals_agg[skill_name_normalized].append(recent_overlap_interval)

                except ValueError as e:
                    logger.warning(f"Skipping experience entry due to date parsing error for recent skills: {e}")
                    continue
        
        # 3. Process each found skill's recent intervals to calculate total recent experience and periods
        final_recent_skills_by_category = defaultdict(list)

        # Iterate through the skills from the original parsed data structure to maintain categorization
        if isinstance(skills_data, dict):
            for category_name, skills_list_in_category in skills_data.items():
                if isinstance(skills_list_in_category, list):
                    for skill_item_dict in skills_list_in_category:
                        if isinstance(skill_item_dict, dict) and skill_item_dict.get('name'):
                            skill_obj = SkillEntry(**skill_item_dict)
                            skill_name_normalized = skill_obj.name.strip().lower()

                            # Get ONLY recent intervals for this skill
                            recent_intervals_for_this_skill = recent_skill_intervals_agg.get(skill_name_normalized, [])

                            if recent_intervals_for_this_skill:
                                merged_recent_intervals = DateUtil.merge_intervals(recent_intervals_for_this_skill)
                                total_recent_years = DateUtil.calculate_total_years(merged_recent_intervals)

                                # Create a new SkillEntry object for the recent overview with only recent periods/years
                                recent_skill_obj = SkillEntry(
                                    name=skill_obj.name,
                                    experience_years=total_recent_years,
                                    periods=[SkillPeriod(from_date=DateUtil.format_date_output(p[0]), to_date=DateUtil.format_date_output(p[1])) for p in merged_recent_intervals]
                                )
                                final_recent_skills_by_category[category_name].append(recent_skill_obj.model_dump(by_alias=True))
                            # else: skill was not active in recent window, so don't include it in recent_skills_overview
        elif isinstance(skills_data, list): # Flat list (e.g., from MatchAIClient)
            for skill_item_dict_or_str in skills_data:
                if isinstance(skill_item_dict_or_str, dict) and skill_item_dict_or_str.get('name'):
                    skill_obj = SkillEntry(**skill_item_dict_or_str)
                    skill_name_normalized = skill_obj.name.strip().lower()
                    recent_intervals_for_this_skill = recent_skill_intervals_agg.get(skill_name_normalized, [])
                    if recent_intervals_for_this_skill:
                        merged_recent_intervals = DateUtil.merge_intervals(recent_intervals_for_this_skill)
                        total_recent_years = DateUtil.calculate_total_years(merged_recent_intervals)
                        recent_skill_obj = SkillEntry(
                            name=skill_obj.name,
                            experience_years=total_recent_years,
                            periods=[SkillPeriod(from_date=DateUtil.format_date_output(p[0]), to_date=DateUtil.format_date_output(p[1])) for p in merged_recent_intervals]
                        )
                        final_recent_skills_by_category["other"].append(recent_skill_obj.model_dump(by_alias=True)) # Default to 'other' category
                elif isinstance(skill_item_dict_or_str, str):
                    skill_name_normalized = skill_item_dict_or_str.strip().lower()
                    recent_intervals_for_this_skill = recent_skill_intervals_agg.get(skill_name_normalized, [])
                    if recent_intervals_for_this_skill:
                        merged_recent_intervals = DateUtil.merge_intervals(recent_intervals_for_this_skill)
                        total_recent_years = DateUtil.calculate_total_years(merged_recent_intervals)
                        recent_skill_obj = SkillEntry(
                            name=skill_name_normalized,
                            experience_years=total_recent_years,
                            periods=[SkillPeriod(from_date=DateUtil.format_date_output(p[0]), to_date=DateUtil.format_date_output(p[1])) for p in merged_recent_intervals]
                        )
                        final_recent_skills_by_category["other"].append(recent_skill_obj.model_dump(by_alias=True)) # Default to 'other' category

        return dict(final_recent_skills_by_category)

    def calculate_organization_switches(self, experience_entries):
        """Calculates the number of unique companies the candidate has worked for."""
        logger.debug(f"calculting organization switches with expereince entries {experience_entries}");
        companies = set()
        for exp in experience_entries:
            if exp.get("company"):
                companies.add(exp["company"].strip())
        return max(0, len(companies) - 1)

    def calculate_technology_experience_years(self, parsed_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculates total experience years for each technology, handling overlaps.
        Prioritizes 'periods' extracted by LLM in skills. If not available,
        falls back to aggregating from experience entries.
        If still no periods, defaults to profile's total career span.
        """
        
        final_aggregated_technology_years = {} 

        # 1. Determine overall profile start date for fallback
        profile_start_date = None
        experience_entries = parsed_data.get('experience', []) # Get experience_entries here
        if experience_entries:
            all_from_dates = []
            for exp in experience_entries:
                # Assuming 'from' and 'to' are consistently present in experience entries
                if exp.get('from'): 
                    try:
                        all_from_dates.append(DateUtil.parse_date_flexible(exp['from']))
                    except ValueError:
                        pass
            if all_from_dates:
                profile_start_date = min(all_from_dates)

        current_date = datetime.now()
        
        # --- Get skills_data, handling different structures ---
        skills_data = parsed_data.get('skills')
        
        # 2. Populate technology_timeframes_from_experience based on parsed experience entries and projects
        technology_timeframes_from_experience = defaultdict(list)
        if experience_entries:
            for exp in experience_entries: # exp is a dictionary
                exp_from = exp.get('from')
                exp_to = exp.get('to')
                exp_technologies = exp.get('technologies', [])
                exp_description = exp.get('description', '').lower()

                if not exp_from or not exp_to:
                    continue

                try:
                    current_job_interval = DateUtil.get_interval(exp_from, exp_to)
                except ValueError as e:
                    logger.warning(f"Skipping experience interval for tech-job linking due to date parsing error: {e}")
                    continue
                
                # Technologies explicitly mentioned in this experience entry
                for tech in exp_technologies:
                    technology_timeframes_from_experience[tech.strip().lower()].append(current_job_interval)
                
                # Also, search for skills from the general skills list within this experience's description
                if isinstance(skills_data, dict):
                    for category_skills_list in skills_data.values():
                        if isinstance(category_skills_list, list):
                            for skill_item_dict_or_str in category_skills_list:
                                if isinstance(skill_item_dict_or_str, dict) and skill_item_dict_or_str.get('name'):
                                    general_skill_name = skill_item_dict_or_str['name'].strip().lower()
                                    if re.search(r'\b' + re.escape(general_skill_name) + r'\b', exp_description, re.IGNORECASE):
                                        technology_timeframes_from_experience[general_skill_name].append(current_job_interval)
                                    elif general_skill_name.replace(' ', '-').lower() in exp_description or \
                                        general_skill_name.replace('-', ' ').lower() in exp_description:
                                        technology_timeframes_from_experience[general_skill_name].append(current_job_interval)
                                elif isinstance(skill_item_dict_or_str, str):
                                    general_skill_name = skill_item_dict_or_str.strip().lower()
                                    if re.search(r'\b' + re.escape(general_skill_name) + r'\b', exp_description, re.IGNORECASE):
                                        technology_timeframes_from_experience[general_skill_name].append(current_job_interval)
                                    elif general_skill_name.replace(' ', '-').lower() in exp_description or \
                                        general_skill_name.replace('-', ' ').lower() in exp_description:
                                        technology_timeframes_from_experience[general_skill_name].append(current_job_interval)
                elif isinstance(skills_data, list): # Flat list of skills
                    for skill_item_dict_or_str in skills_data:
                        if isinstance(skill_item_dict_or_str, dict) and skill_item_dict_or_str.get('name'):
                            general_skill_name = skill_item_dict_or_str['name'].strip().lower()
                            if re.search(r'\b' + re.escape(general_skill_name) + r'\b', exp_description, re.IGNORECASE):
                                technology_timeframes_from_experience[general_skill_name].append(current_job_interval)
                            elif general_skill_name.replace(' ', '-').lower() in exp_description or \
                                general_skill_name.replace('-', ' ').lower() in exp_description:
                                technology_timeframes_from_experience[general_skill_name].append(current_job_interval)
                        elif isinstance(skill_item_dict_or_str, str):
                            general_skill_name = skill_item_dict_or_str.strip().lower()
                            if re.search(r'\b' + re.escape(general_skill_name) + r'\b', exp_description, re.IGNORECASE):
                                technology_timeframes_from_experience[general_skill_name].append(current_job_interval)
                            elif general_skill_name.replace(' ', '-').lower() in exp_description or \
                                general_skill_name.replace('-', ' ').lower() in exp_description:
                                technology_timeframes_from_experience[general_skill_name].append(current_job_interval)

        # Technologies explicitly mentioned in projects with durations
        if parsed_data.get('projects'):
            for project in parsed_data['projects']:
                if project.get('technologies') and project.get('from_date') and project.get('to_date'):
                    try:
                        project_interval = DateUtil.get_interval(project['from_date'], project['to_date'])
                        for tech in project['technologies']:
                            technology_timeframes_from_experience[tech.strip().lower()].append(project_interval)
                    except ValueError as e:
                        logger.warning(f"Skipping project interval for project '{project.get('name', 'N/A')}' due to date parsing error: {e}")


        # 3. Process each SkillEntry to populate its 'periods' and 'experience_years'
        if isinstance(skills_data, dict): 
            for category_name, skills_list_in_category in skills_data.items():
                if isinstance(skills_list_in_category, list):
                    for i, skill_item_dict in enumerate(skills_list_in_category):
                        if isinstance(skill_item_dict, dict) and skill_item_dict.get('name'):
                            # Create Pydantic object from dict for manipulation
                            skill_obj = SkillEntry(**skill_item_dict) 
                            skill_name_normalized = skill_obj.name.strip().lower()

                            # Combine LLM-extracted periods with job experience periods
                            combined_intervals_for_skill = []
                            if skill_obj.periods: # Start with LLM extracted periods (if any)
                                for p in skill_obj.periods:
                                    try:
                                        combined_intervals_for_skill.append(DateUtil.get_interval(p.from_date, p.to_date))
                                    except ValueError as e:
                                        logger.warning(f"Skipping LLM-extracted period for '{skill_name_normalized}' due to date error: {e}")
                            
                            # Add intervals derived from job experiences where this skill was used
                            # This covers skills explicitly in exp.technologies or identified in exp.description
                            combined_intervals_for_skill.extend(technology_timeframes_from_experience.get(skill_name_normalized, []))

                            if combined_intervals_for_skill:
                                merged_intervals = DateUtil.merge_intervals(combined_intervals_for_skill)
                                total_years = DateUtil.calculate_total_years(merged_intervals)
                                
                                skill_obj.experience_years = total_years 
                                skill_obj.periods = [SkillPeriod(from_date=DateUtil.format_date_output(p[0]), to_date=DateUtil.format_date_output(p[1])) for p in merged_intervals]
                            else:
                                # CRITICAL NEW LOGIC: If periods are still empty/None after all attempts, default to profile span
                                if profile_start_date: # Only if profile start date is valid
                                    skill_obj.experience_years = DateUtil.calculate_total_years([(profile_start_date, current_date)])
                                    skill_obj.periods = [SkillPeriod(from_date=DateUtil.format_date_output(profile_start_date), to_date=DateUtil.format_date_output(current_date))]
                                    logger.info(f"Skill '{skill_name_normalized}' periods were empty, defaulting to profile start to current date.")
                                else: # No periods found and no profile start date fallback
                                    skill_obj.experience_years = 0.0
                                    skill_obj.periods = []
                                    logger.warning(f"Skill '{skill_name_normalized}' periods were empty and no profile start date found. Defaulted to 0 years.")

                            # Update the original dict in parsed_data with the modified Pydantic object's dict
                            skills_list_in_category[i] = skill_obj.model_dump(by_alias=True)
                            final_aggregated_technology_years[skill_name_normalized] = skill_obj.experience_years
                        
                        elif isinstance(skill_item_dict, str): # Fallback for simple string skill (no periods/years)
                            skill_name_normalized = skill_item_dict.strip().lower()
                            # For simple string skills, they don't have a 'periods' field to update.
                            # We just calculate their total_years based on derived intervals or fallback.
                            if skill_name_normalized in technology_timeframes_from_experience:
                                merged_intervals = DateUtil.merge_intervals(technology_timeframes_from_experience[skill_name_normalized])
                                total_years = DateUtil.calculate_total_years(merged_intervals)
                                final_aggregated_technology_years[skill_name_normalized] = total_years
                            else:
                                if profile_start_date:
                                    final_aggregated_technology_years[skill_name_normalized] = DateUtil.calculate_total_years([(profile_start_date, current_date)])
                                    logger.info(f"Plain skill '{skill_name_normalized}' had no explicit periods, defaulting to profile start to current date.")
                                else:
                                    final_aggregated_technology_years[skill_name_normalized] = 0.0
                                    logger.warning(f"Plain skill '{skill_name_normalized}' had no explicit periods and no profile start date. Defaulted to 0 years.")

        elif isinstance(skills_data, list): # If it's a flat list (e.g., from MatchAIClient)
            for skill_item_dict_or_str in skills_data:
                # If skills are flat list, we don't have 'periods' field to populate directly in the output.
                # Just calculate final_aggregated_technology_years.
                if isinstance(skill_item_dict_or_str, dict) and skill_item_dict_or_str.get('name'):
                    skill_name_normalized = skill_item_dict_or_str['name'].strip().lower()
                    if skill_name_normalized in technology_timeframes_from_experience:
                        merged_intervals = DateUtil.merge_intervals(technology_timeframes_from_experience[skill_name_normalized])
                        total_years = DateUtil.calculate_total_years(merged_intervals)
                        final_aggregated_technology_years[skill_name_normalized] = total_years
                    else:
                        if profile_start_date:
                            final_aggregated_technology_years[skill_name_normalized] = DateUtil.calculate_total_years([(profile_start_date, current_date)])
                            logger.info(f"Flat dict skill '{skill_name_normalized}' had no periods, defaulting to profile start to current date.")
                        else:
                            final_aggregated_technology_years[skill_name_normalized] = 0.0
                            logger.warning(f"Flat dict skill '{skill_name_normalized}' had no periods and no profile start date. Defaulted to 0 years.")
                elif isinstance(skill_item_dict_or_str, str):
                    skill_name_normalized = skill_item_dict_or_str.strip().lower()
                    if skill_name_normalized in technology_timeframes_from_experience:
                        merged_intervals = DateUtil.merge_intervals(technology_timeframes_from_experience[skill_name_normalized])
                        total_years = DateUtil.calculate_total_years(merged_intervals)
                        final_aggregated_technology_years[skill_name_normalized] = total_years
                    else:
                        if profile_start_date:
                            final_aggregated_technology_years[skill_name_normalized] = DateUtil.calculate_total_years([(profile_start_date, current_date)])
                            logger.info(f"Flat string skill '{skill_name_normalized}' had no periods, defaulting to profile start to current date.")
                        else:
                            final_aggregated_technology_years[skill_name_normalized] = 0.0
                            logger.warning(f"Flat string skill '{skill_name_normalized}' had no periods and no profile start date. Defaulted to 0 years.")
        
        return final_aggregated_technology_years
    
    def calculate_technology_experience_yearsV1(self, parsed_data):
        """
        Calculates total experience years for each technology, handling overlaps.
        Assumes parsed_data has 'skills', 'experience', and 'projects' keys.
        The 'skills' part can now contain objects like {"name": "Java", "experience_years": 5}.
        """
        logger.debug(f"calculate_technology_experience_years*******")
        logger.debug(f"{parsed_data}")
        logger.debug(f"calculate_technology_experience_years*******END")
        technology_timeframes = defaultdict(list)

        skills_data = parsed_data.get('skills', {})
        if skills_data:
            all_skill_names = [] # We need to collect just the names for this calculation logic
            for category_skills in skills_data.values():
                if isinstance(category_skills, list):
                    for skill_item in category_skills:
                        if isinstance(skill_item, dict) and skill_item.get('name'):
                            all_skill_names.append(skill_item['name'])
                        elif isinstance(skill_item, str): # Fallback for old string format
                            all_skill_names.append(skill_item)
            
            for skill_name_str in all_skill_names: # Iterate through the extracted skill names
                normalized_skill = skill_name_str.strip().lower() # Now skill_name_str is a string
                # The rest of the logic associates job/project durations with this skill name
                for exp in parsed_data.get('experience', []):
                    if exp.get('from') and exp.get('to'):
                        try:
                            # Check if this skill is mentioned in the experience's technologies
                            # or if we should associate all general skills with all experiences
                            # For now, let's assume general skills apply to all experiences
                            # A more refined logic might only link if skill is in exp['technologies']
                            interval = DateUtil.get_interval(exp['from'], exp['to'])
                            technology_timeframes[normalized_skill].append(interval)
                        except ValueError as e:
                            logger.warning(f"Skipping exp interval for skill '{normalized_skill}' due to date parsing error: {e}")

        # This part is for technologies explicitly mentioned in projects with durations
        if parsed_data.get('projects'):
            for project in parsed_data['projects']:
                if project.get('technologies') and project.get('from') and project.get('to'):
                    try:
                        project_interval = DateUtil.get_interval(project['from'], project['to'])
                        for tech in project['technologies']:
                            normalized_tech = tech.strip().lower()
                            # This will add or append to existing intervals for the tech
                            technology_timeframes[normalized_tech].append(project_interval)
                    except ValueError as e:
                        logger.warning(f"Skipping project interval for project '{project.get('name', 'N/A')}' due to date parsing error: {e}")

        final_technology_experience_years = {}
        for tech, intervals in technology_timeframes.items():
            if not intervals: # Ensure there are intervals before merging
                continue
            merged = DateUtil.merge_intervals(intervals)
            years = DateUtil.calculate_total_years(merged)
            final_technology_experience_years[tech] = years
            
        return final_technology_experience_years

    def calculate_time_spent_in_organizations_v2(self, experience_entries):
        """
        Calculates the time spent in each unique organization.
        Aggregates durations for multiple roles within the same company.
        Assumes experience_entries use 'start_date' and 'end_date' for dates.
        Returns a list of dictionaries with 'company_name', 'total_duration_years', and 'total_duration_months'.
        """
        company_durations = defaultdict(list)

        for exp in experience_entries:
            company_name = exp.get('company')
            if not company_name or not exp.get('start_date') or not exp.get('end_date'):
                continue

            try:
                # CRITICAL CHANGE: Use 'start_date' and 'end_date'
                interval = DateUtil.get_interval(exp['start_date'], exp['end_date'])
                company_durations[company_name.strip()].append(interval)
            except ValueError as e:
                logger.warning(f"Could not parse dates for experience at '{company_name}' using 'start_date'/'end_date' due to error: {e}")
                continue

        result = []
        for company, intervals in company_durations.items():
            merged_intervals = DateUtil.merge_intervals(intervals)
            total_duration_days = 0
            for start, end in merged_intervals:
                total_duration_days += (end - start).days

            total_duration_years = round(total_duration_days / 365.25, 2)
            total_duration_months = round(total_duration_days / (365.25 / 12), 2)

            result.append({
                "company_name": company,
                "total_duration_years": total_duration_years,
                "total_duration_months": total_duration_months
            })
        
        result.sort(key=lambda x: x['total_duration_years'], reverse=True)
        
        return result
    
    def calculate_time_spent_in_organizations(self, experience_entries):
        """
        Calculates the time spent in each unique organization.
        Aggregates durations for multiple roles within the same company.
        Returns a list of dictionaries with 'company_name', 'total_duration_years', and 'total_duration_months'.
        """
        company_durations = defaultdict(list)

        for exp in experience_entries:
            company_name = exp.get('company')
            if not company_name or not exp.get('from') or not exp.get('to'):
                continue

            try:
                interval = DateUtil.get_interval(exp['from'], exp['to'])
                company_durations[company_name.strip()].append(interval)
            except ValueError as e:
                logger.warning(f"Could not parse dates for experience at '{company_name}' due to error: {e}")
                continue

        result = []
        for company, intervals in company_durations.items():
            merged_intervals = DateUtil.merge_intervals(intervals)
            total_duration_days = 0
            for start, end in merged_intervals:
                total_duration_days += (end - start).days

            total_duration_years = round(total_duration_days / 365.25, 2)
            total_duration_months = round(total_duration_days / (365.25 / 12), 2)

            result.append({
                "company_name": company,
                "total_duration_years": total_duration_years,
                "total_duration_months": total_duration_months
            })
        
        result.sort(key=lambda x: x['total_duration_years'], reverse=True)
        
        return result

    def calculate_total_experience(self, experience_entries):
        """
        Calculates the candidate's total professional experience in years.
        Merges all experience intervals to avoid double-counting overlapping periods.
        """
        all_intervals = []
        for exp in experience_entries:
            if exp.get('from') and exp.get('to'):
                try:
                    interval = DateUtil.get_interval(exp['from'], exp['to'])
                    all_intervals.append(interval)
                except ValueError as e:
                    logger.warning(f"Skipping experience interval for total experience calculation due to date parsing error: {e}")
        
        if not all_intervals:
            return 0.0

        merged_intervals = DateUtil.merge_intervals(all_intervals)
        total_years = DateUtil.calculate_total_years(merged_intervals)
        return total_years
    
    # NEW METHOD: calculate_current_job_tenure
    def calculate_current_job_tenure(self, parsed_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Identifies the current (most recent and ongoing) job role and calculates its tenure.
        Returns a tuple: (current_company, current_title, current_tenure_years).
        """
        current_company = None
        current_title = None
        current_tenure_years = None
        
        experience_entries = parsed_data.get('experience', [])
        
        # Sort experiences to find the most recent one
        # Assuming 'to' date 'Present' is latest, otherwise sort by 'to' date descending
        latest_experience = None
        latest_to_date = datetime.min # For sorting if no 'Present'

        for exp in experience_entries:
            to_date_str = exp.get('to')
            if to_date_str and to_date_str.lower() == 'present':
                latest_experience = exp
                break # Found the 'Present' job, this is the current one
            else:
                try:
                    current_exp_to_date = DateUtil.parse_date_flexible(to_date_str)
                    if current_exp_to_date > latest_to_date:
                        latest_to_date = current_exp_to_date
                        latest_experience = exp
                except ValueError:
                    pass # Ignore invalid dates

        if latest_experience:
            current_company = latest_experience.get('company')
            current_title = latest_experience.get('title')
            
            # Calculate tenure for this latest experience
            from_date_str = latest_experience.get('from')
            to_date_str = latest_experience.get('to') # Will be 'Present' or a specific date

            if from_date_str and to_date_str:
                try:
                    start_date = DateUtil.parse_date_flexible(from_date_str)
                    end_date = DateUtil.parse_date_flexible(to_date_str)
                    
                    if to_date_str.lower() == 'present':
                        end_date = datetime.now() # Use current date for calculation

                    current_tenure_years = round((end_date - start_date).days / 365.25, 2)
                except ValueError as e:
                    logger.warning(f"Could not calculate current tenure for {current_company} - {current_title} due to date parsing error: {e}")
        
        logger.info(f"Calculated current job tenure: Company={current_company}, Title={current_title}, Tenure={current_tenure_years} years.")
        return current_company, current_title, current_tenure_years    